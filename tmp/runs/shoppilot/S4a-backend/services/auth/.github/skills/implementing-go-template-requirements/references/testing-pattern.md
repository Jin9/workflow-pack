# Testing pattern

**Unit-test scope**: boundary code (`handler_<action>.go`, `consumer_<action>.go`) and the service layer (`service_<action>.go`). The constructor (`NewHandler`/`New*`), the access layer (`storage_*`/`cache_*`/`client_*`), generated `mocks/`, and domain-model getters are **out of scope** under this skill. Coverage target: **100% statement coverage of in-scope functions** in the `app/<domain>/` package (constructors and the `access/` sub-package excluded).

**Test package by layer** — both kinds of test file coexist in the same directory:

- **Boundary tests** (handler/consumer) → external `package <domain>_test`. They call **exported** methods (`h.<Action>`, `h.On<Action>`).
- **Service tests** → internal `package <domain>`. Service helpers are **unexported** `*handler` methods, reachable only from inside the package.

## The shape: `mockArgs` / `args` / `want` / `prepare` + table

The pattern is the same for handlers, consumers, and services — only the package declaration and the act/assert blocks differ.

```go
package <domain>_test

import (
    "bytes"
    "context"
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "gitlab.com/.../common/app"
    "gitlab.com/.../common/wrapper"
    access_mocks "gitlab.com/.../app/<domain>/access/mocks"

    "gitlab.com/.../app/<domain>"
    "gitlab.com/.../app/<domain>/access"

    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
)

func Test<Action>(t *testing.T) {
    r := require.New(t)

    // Local types — keep them inside the test function for scope clarity.
    type mockArgs struct {
        <dep>Storage *access_mocks.<Dep>StorageMock
        // add other mocks as needed
    }

    type args struct {
        ctx context.Context
        req <domain>.<Action>Request
    }

    type want struct {
        err     bool
        code    app.Code
        Message app.Message
        data    wrapper.ResponseOption[<domain>.<Action>Response]
    }

    tests := []struct {
        name    string
        prepare func(m mockArgs, args args)
        args    args
        want    want
    }{
        // success
        {
            name: "success, case valid request",
            prepare: func(m mockArgs, args args) {
                m.<dep>Storage.
                    EXPECT().
                    <Method>(args.ctx, mock.Anything).
                    Return(access.<Model>{<ModelID>: uuid.New().String()}, nil)
            },
            args: args{
                req: <domain>.<Action>Request{ /* valid fields */ },
            },
            want: want{
                err:     false,
                code:    app.CodeSuccess,
                Message: app.MessageSuccess,
            },
        },

        // each missing-required-field case
        {
            name: "fail, case invalid request body - missing <field>",
            prepare: func(m mockArgs, args args) { /* no storage call expected */ },
            args: args{
                req: <domain>.<Action>Request{ /* missing the field */ },
            },
            want: want{
                err:     true,
                code:    app.CodeBadRequest,
                Message: app.MessageBadRequest,
            },
        },

        // each downstream error
        {
            name: "fail, case <Method> storage error",
            prepare: func(m mockArgs, args args) {
                m.<dep>Storage.
                    EXPECT().
                    <Method>(args.ctx, mock.Anything).
                    Return(access.<Model>{}, assert.AnError)
            },
            args: args{ req: <domain>.<Action>Request{ /* valid */ } },
            want: want{
                err:     true,
                code:    app.CodeInternalError,
                Message: app.MessageInternalError,
            },
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            w := httptest.NewRecorder()
            ctx, _ := gin.CreateTestContext(w)

            // Arrange request body
            var payload bytes.Buffer
            json.NewEncoder(&payload).Encode(tt.args.req)
            req := httptest.NewRequest(http.MethodPost, "http://0.0.0.0/api/v1/platform/<domain>/<action>", &payload)
            req.Header.Set("Content-Type", "application/json")
            ctx.Request = req

            // Construct mocks
            m := mockArgs{
                <dep>Storage: access_mocks.New<Dep>StorageMock(t),
            }

            // IMPORTANT: assign ctx BEFORE calling prepare — mock matchers may capture it.
            if tt.prepare != nil {
                tt.args.ctx = ctx.Request.Context()
                tt.prepare(m, tt.args)
            }

            h := <domain>.NewHandler(<domain>.HandlerConfig{
                <Dep>Storage: m.<dep>Storage,
            })

            // Act
            h.<Action>(ctx)

            // Assert
            var resp wrapper.ResponseOption[<domain>.<Action>Response]
            json.NewDecoder(w.Body).Decode(&resp)

            if tt.want.err {
                r.NotEqual(http.StatusOK, w.Code)
                r.Equal(tt.want.code, resp.Code)
                r.Equal(tt.want.Message, resp.Message)
            } else {
                r.Equal(http.StatusOK, w.Code)
                r.Equal(tt.want.code, resp.Code)
                r.Equal(tt.want.Message, resp.Message)
            }
        })
    }
}
```

## Kafka consumer variant

Replace the Act/Assert section with:

```go
// Arrange — marshal payload into a kafka.Message[json.RawMessage]
payloadBytes, _ := json.Marshal(tt.args.payload)
msg := kafka.Message[json.RawMessage]{
    EventID: "test-event-id",
    Payload: payloadBytes,
}

// Construct handler
h := <domain>.NewHandler(<domain>.HandlerConfig{
    <Dep>Storage: m.<dep>Storage,
})

// Act
err := h.On<Action>(tt.args.ctx, msg)

// Assert
if tt.want.err {
    r.Error(err)
} else {
    r.NoError(err)
}
```

For invalid-JSON cases, set `msg.Payload = []byte("{ invalid")` and expect an error.
For validation-failure cases, marshal a struct that omits a `binding:"required"` field and expect an error.

## Service-layer variant (internal package)

Service helpers are **unexported** `*handler` methods (`func (h *handler) applyPromo(ctx, …)`), so their test file must declare the **internal** `package <domain>` — not `<domain>_test`. Build the handler with mocks, call the method directly, and assert on the returned `(value, error)`. No gin context, no HTTP.

```go
package <domain> // internal — NOT <domain>_test

func Test_<action>(t *testing.T) {
    // ... fixtures: uuid.New(), access.<Model>{...}

    type mockArgs struct {
        <dep>Storage *access_mocks.<Dep>StorageMock
    }
    type args struct {
        ctx context.Context
        // service params after ctx (promoID, memberID, …)
    }
    type want struct {
        result <ResultType>
        err    error // a sentinel to assert with errors.Is, or nil for success
    }

    tests := []struct {
        name    string
        prepare func(m mockArgs, ctx context.Context)
        args    args
        want    want
    }{
        // success + one case per sentinel error + one case per `if err != nil`
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            r := require.New(t)
            m := mockArgs{<dep>Storage: access_mocks.New<Dep>StorageMock(t)}

            tt.args.ctx = context.Background() // assign BEFORE prepare so matchers see it
            tt.prepare(m, tt.args.ctx)

            // Unqualified — the test is in the same package, so it can build *handler
            // and call the unexported method.
            h := NewHandler(HandlerConfig{<Dep>Storage: m.<dep>Storage})

            got, err := h.<action>(tt.args.ctx /*, params */)

            if tt.want.err != nil {
                r.ErrorIs(err, tt.want.err)
                return
            }
            r.NoError(err)
            r.Equal(tt.want.result, got)
        })
    }
}
```

Cover the success path, each sentinel error the helper returns (assert with `errors.Is`), and every `if err != nil` from an access call. A best-effort side effect (e.g. a fire-and-forget Kafka publish that swallows its own error) still needs a case that drives its branch.

## Coverage rules

These branches MUST have a test case each:

- Every `if err != nil` block in the handler/consumer/service body.
- Every `binding:"required"` field on the request/payload struct (one missing-field case per).
- Every model-getter call the handler/service branches on — e.g. `GetID()` parsing a string field as UUID. Feed a deliberately bad string so the **handler's/service's** `if err != nil` branch runs. You are covering that branch, not the getter (the getter lives in `access/`, which is out of scope).
- For Kafka consumers: invalid JSON (`{ invalid`) and validation-failure cases.
- The success path.

Verify with (the filters drop the out-of-scope access layer and constructors):

```bash
go test -race -coverprofile=coverage.out ./app/<domain>/...
go tool cover -func=coverage.out \
  | grep '/app/<domain>/' \
  | grep -v '/access/' \   # access layer is out of scope
  | grep -v '	New' \       # leading TAB then New… exempts constructors
  | grep -v '100.0%'       # must print NOTHING
```

The final pipeline should print nothing — every in-scope function (handlers, consumers, services) at 100%. The tab before `New` matches the function-name column of `go tool cover -func` output, so only constructors (`NewHandler`, `New<Dep>Storage`, …) are filtered, not methods like `OnOrderCancelled`.

## Mock-builder API

Mocks are generated by `mockery` per the repo's `.mockery.yaml`. **Do not hand-edit** them.

Pattern:

```go
m := access_mocks.NewMemberStorageMock(t)

m.EXPECT().
    GetMemberByEmail(ctx, hashedEmail).
    Return(access.Member{MemberID: id.String()}, nil)

m.EXPECT().
    GetMemberByEmail(mock.Anything, mock.MatchedBy(func(s string) bool {
        return len(s) > 0
    })).
    Return(access.Member{}, assert.AnError)
```

After changing an interface, regenerate mocks:

```bash
mockery
```

(or `go generate ./...` if a `//go:generate` directive is in use).

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| Test stalls on `mock.MatchedBy` | `args.ctx` not assigned before `prepare` is called | Move `tt.args.ctx = ctx.Request.Context()` BEFORE `tt.prepare(m, tt.args)`. |
| Mock returns wrong type | Stale mock after interface change | Regenerate with `mockery`. |
| Coverage stuck at 95% | Missing test for a `GetID()` parse failure | Add a case where the storage returns a model with a deliberately invalid UUID string. |
| `json.Unmarshal` worked in handler test but consumer rejects valid payload | Consumer uses `kafka.BindMessage` (correct) which runs binding tags | Verify the test marshals a payload that satisfies all `binding` tags. |
| `make test` passes but `make precommit` fails on lint | Mocks file unformatted, or test file imports out of order | Run `go fmt` and `goimports`. Do not modify `.golangci.yaml` to silence. |
