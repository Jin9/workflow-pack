# Common-module quick reference

The shared infrastructure lives in the **`common`** module. Services **import** it — never vendor or copy. This page summarises the helpers business logic uses every day, with the canonical call shape and the rule that constrains usage.

## `wrapper` — HTTP request binding and response shaping

### `wrapper.BindJSON[T any](c *gin.Context, attrs ...slog.Attr) (T, bool)`

Bind a JSON body into a typed struct, validate `binding:` tags, and emit a 400 response automatically if binding fails. Returns the parsed value and a boolean. If `false`, the response is already written — return from the handler.

```go
req, ok := wrapper.BindJSON[CreateProductRequest](c, slog.String("handler", "CreateProduct"))
if !ok {
    return
}
```

### `wrapper.ResponseOption[T any]`

The response envelope. Use it as the type argument when responding.

```go
type ResponseOption[T any] struct {
    HTTPStatus int
    Code       app.Code
    Message    app.Message
    Data       *T
    Err        error
}
```

### `wrapper.Respond(c *gin.Context, opt wrapper.ResponseOption[T])`

Writes the response. Use this — do not call `c.JSON` directly.

```go
wrapper.Respond(c, wrapper.ResponseOption[CreateProductResponse]{
    HTTPStatus: http.StatusCreated,
    Code:       app.CodeSuccess,
    Message:    app.MessageSuccess,
    Data:       &CreateProductResponse{ProductID: created.ProductID},
})
```

Error case:

```go
wrapper.Respond(c, wrapper.ResponseOption[CreateProductResponse]{
    HTTPStatus: http.StatusInternalServerError,
    Code:       app.CodeInternalError,
    Message:    app.MessageInternalError,
    Err: serror.Wrap(err).With(
        slog.String("product_name", req.Name),
    ),
})
```

## `app` — response codes and messages

Use the `app.Code*` and `app.Message*` constants when populating `ResponseOption`. Common pairs:

| HTTPStatus | Code | Message |
|---|---|---|
| `http.StatusOK` / `http.StatusCreated` | `app.CodeSuccess` | `app.MessageSuccess` |
| `http.StatusBadRequest` | `app.CodeBadRequest` | `app.MessageBadRequest` |
| `http.StatusUnauthorized` | `app.CodeUnauthorized` | `app.MessageUnauthorized` |
| `http.StatusForbidden` | `app.CodeForbidden` | `app.MessageForbidden` |
| `http.StatusNotFound` | `app.CodeNotFound` | `app.MessageNotFound` |
| `http.StatusInternalServerError` | `app.CodeInternalError` | `app.MessageInternalError` |

Do NOT invent ad-hoc string codes or messages. If you need a new pair, that is a config change to the common module — out of scope under this skill.

## `serror` — structured error wrapping at handler/consumer/service layer

`serror.Wrap(err).With(slog.Attr...)` enriches an error with source location and structured attributes.

```go
return serror.Wrap(err).With(
    slog.String("event_id", msg.EventID),
    slog.String("member_id", memberID.String()),
)
```

**Rule of layer**:

- Access layer wraps with `fmt.Errorf("...: %w", err)`. NO serror.
- Handler / consumer / service layer wraps with `serror.Wrap(err).With(...)`. Always attach context attrs.

## `kafka` — consumer payload binding

### `kafka.Message[json.RawMessage]`

The incoming message wrapper. The `Payload` is raw bytes you must bind.

### `kafka.BindMessage(payload json.RawMessage, target any) error`

Deserialise AND validate against `binding:` tags. Use this — **never** `json.Unmarshal`. Plain `Unmarshal` silently accepts payloads that violate `binding:"required"`.

```go
var payload CreateProductMessage
if err := kafka.BindMessage(msg.Payload, &payload); err != nil {
    return serror.Wrap(err).With(slog.String("event_id", msg.EventID))
}
```

### Consumer signature

Always:

```go
func (h *handler) On<Action>(ctx context.Context, msg kafka.Message[json.RawMessage]) error
```

Return `nil` on success, `serror.Wrap(err)` chain on failure. The subscriber lifecycle handles retries/DLQ.

## `logger` — structured logging via `log/slog`

Initialised once in `main.go`. Business logic uses `log/slog` calls directly:

```go
slog.InfoContext(ctx, "issued token",
    slog.String("member_id", memberID.String()),
    slog.String("organization_id", orgID.String()),
)
```

Do NOT create a new logger. Do NOT use third-party loggers (zap, zerolog, logrus). Do NOT use `log.Printf`.

## `hash`, `crypt`, `token` — security primitives

Injected into `HandlerConfig` from the composition root (`router/deps.go`, which is FORBIDDEN to edit under this skill). Use the interfaces directly:

- `hash.HashManager.Hash(input string) string` — deterministic hashing (e.g. for hashed email lookup).
- `crypt.Cipher.Encrypt(plaintext string) (string, error)` / `.Decrypt(ciphertext string) (string, error)`.
- `token.JWTSigner.SignES256(claims token.Claims) (string, error)`.

If the requirement needs a new security primitive that does not exist in the common module — STOP. That is out of scope under this skill.

## What you do NOT call directly

These are wired by the scaffold and used only inside `access/`:

- Firestore client (`gcpfirestore.Client`) — used by `storage_*.go` only.
- MySQL `*sql.DB` — used by `storage_*.go` only.
- Redis client — used by `cache_*.go` only.
- `*http.Client` — used by `client_*.go` only.

Handlers and consumers go through `access/` interfaces. Never call SDK methods from a handler.

## The error layering example end-to-end

```go
// access/storage_product.go (access layer)
func (s *productStorage) CreateProduct(ctx context.Context, p Product) (Product, error) {
    _, err := s.fs.Collection(productCollection).Doc(p.ProductID).Set(ctx, p)
    if err != nil {
        return Product{}, fmt.Errorf("failed to create product: %w", err)
    }
    return p, nil
}

// handler_create.go (handler layer)
created, err := h.productStorage.CreateProduct(ctx, product)
if err != nil {
    wrapper.Respond(c, wrapper.ResponseOption[CreateProductResponse]{
        HTTPStatus: http.StatusInternalServerError,
        Code:       app.CodeInternalError,
        Message:    app.MessageInternalError,
        Err: serror.Wrap(err).With(
            slog.String("product_name", req.Name),
        ),
    })
    return
}
```

Two wrappings: `fmt.Errorf("...: %w", err)` at access, `serror.Wrap(err).With(...)` at handler. The full chain is preserved.
