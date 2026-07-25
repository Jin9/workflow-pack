# Verification checklist

Run **before** declaring the requirement done. Every box must be ticked. Any failure means more work — do not claim completion.

## A. Scaffold lock (the hard gate)

- [ ] `git diff --name-only` against your base branch shows ONLY:
  - paths under `app/<domain>/`, OR
  - `router/router.go` with edits confined to a single `register<Domain>Routes` block, OR
  - `router/subscriber.go` with edits confined to `registerEventRoutes`, OR
  - `spec.md` with a new endpoint/event entry.
- [ ] No edits to: `main.go`, `config/`, `router/deps.go`, `Makefile`, `Dockerfile`, `docker-compose.yml`, `gitlabci.yml`, `.github/`, `.scripts/`, `.golangci.yaml`, `.mockery.yaml`, `.env.template`, `VERSION`, `CHANGELOG.md`, `go.mod`, `go.sum`.

If A fails: revert the leaked file. Re-check why the scaffold-lock policy did not catch it before you wrote — that is a process bug, not a code bug.

## B. Naming and structure

- [ ] All new files match the prefix table: `handler_<action>.go`, `consumer_<action>.go`, `service_<action>.go`, `storage_<dep>.go`, `cache_<dep>.go`, `client_<dep>.go`.
- [ ] One package per aggregate; no cross-domain imports introduced.
- [ ] No new `model.go`, `errors.go`, `constants.go`, `types.go`, or `util.go` inside any `access/` folder.
- [ ] Every new test file pairs 1:1 with a code file (`handler_create.go` ↔ `handler_create_test.go`).

## C. Code conventions

- [ ] `var _ <Interface> = (*<impl>)(nil)` compile-time check on every new impl.
- [ ] Constructor returns the interface; impl struct is unexported.
- [ ] Every I/O method takes `ctx context.Context` as its first arg.
- [ ] Every new or modified function has **≤3 parameters after `ctx`**. 4+ → Introduce Parameter Object (`<Action>Params`) before merging.
- [ ] Every new or modified function returns **`(T, error)`**, or one of the named exceptions: `(T, bool)` for lookup-style "found" checks, or naked `error` for I/O with no value. 3+ returns → Introduce Result Object (`<Action>Result`).
- [ ] Access-layer errors use `fmt.Errorf("...: %w", err)`.
- [ ] Handler / consumer / service errors use `serror.Wrap(err).With(slog.Attr...)`.
- [ ] HTTP handlers use `wrapper.BindJSON[T]` + `wrapper.Respond` with `app.Code*` / `app.Message*` constants.
- [ ] Kafka consumers use `kafka.BindMessage`; signature `func(ctx context.Context, msg kafka.Message[json.RawMessage]) error`.
- [ ] Routes follow `/api/v1/<domain>/<aggregate>/<action>`; event names follow `<DOMAIN>_<AGGREGATE>_<ACTION>` (UPPER_SNAKE).
- [ ] No third-party loggers introduced; only `log/slog`.
- [ ] No `json.Unmarshal` used in a Kafka consumer.

## D. Tests

- [ ] Unit-test scope = handlers + consumers + services. **No** unit tests for the constructor (`New*`) or the `access/` layer (`storage_*`/`cache_*`/`client_*`) — both are out of scope under this skill.
- [ ] Boundary tests (handler/consumer) in external `package <domain>_test`; service tests in internal `package <domain>` (service helpers are unexported `*handler` methods).
- [ ] `mockArgs` / `args` / `want` / `prepare` pattern followed.
- [ ] Success case present.
- [ ] One failing-validation case per `binding:"required"` field on the request or payload struct.
- [ ] One case per `if err != nil` branch in the handler/consumer/service body.
- [ ] Each sentinel error a service helper returns has a case (assert with `errors.Is`).
- [ ] Model-getter parse failures covered (a bad UUID drives the handler's/service's error branch, not the getter itself).
- [ ] For Kafka consumers: invalid-JSON case AND validation-failure case both present.
- [ ] Mocks regenerated via `mockery` — no hand-edits to `access/mocks/mocks.go`.

## E. Coverage (in-scope only)

- [ ] `go test -race -coverprofile=coverage.out ./app/<domain>/...` exits 0.
- [ ] In-scope coverage gate prints nothing — the `access/` sub-package and constructors (`New*`) are filtered out:
  ```bash
  go tool cover -func=coverage.out | grep '/app/<domain>/' | grep -v '/access/' | grep -v '	New' | grep -v '100.0%'
  ```
  (The leading tab before `New` matches the function-name column; full explanation in `references/testing-pattern.md`.)

## F. Build gates

- [ ] `make precommit` (or equivalent) passes:
  - `go fmt ./...` — clean.
  - `go vet ./...` — clean.
  - `golangci-lint run` — clean (no rules disabled or silenced).
  - `go test -race -cover ./...` — green.

## G. Documentation

- [ ] If a new HTTP endpoint or Kafka event was added, `spec.md` documents:
  - Method + path (HTTP) or event name (Kafka).
  - Request/payload schema with field types and required flags.
  - Response schema with success and error shapes.
- [ ] No reformatting of unrelated `spec.md` sections.

## H. Commit hygiene (if you commit)

- [ ] One commit per logical change — do NOT bundle feature work with refactoring.
- [ ] Commit message references the requirement (ticket/spec section).
- [ ] No commits touching FORBIDDEN files.

## Diff allowlist quick check

Run this snippet at the end:

```bash
# Show only paths and classify
git diff --name-only $(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main) | while read f; do
  case "$f" in
    app/*/*)                     echo "ALLOWED  $f" ;;
    router/router.go)            echo "NARROW   $f" ;;
    router/subscriber.go)        echo "NARROW   $f" ;;
    spec.md)                     echo "NARROW   $f" ;;
    *)                           echo "FORBIDDEN $f" ;;
  esac
done
```

Any line starting with `FORBIDDEN` means the gate failed — revert and re-plan.

## Failure modes and remediation

| Failure | Remediation |
|---|---|
| FORBIDDEN file in diff | Revert it (`git checkout -- <file>`). Re-check the requirement: did Step 4 of the workflow correctly classify all files? If the requirement legitimately needs the scaffold edit, surface to the user and ask. |
| In-scope coverage < 100% | Identify the uncovered branch with `go tool cover -html=coverage.out`. Add the missing test case using the `mockArgs`/`args`/`want`/`prepare` template. If the uncovered line is a constructor (`New*`) or an `access/` method, it is out of scope — ignore it. |
| Lint failure that involves business-logic style | Fix the code. Do NOT silence the rule. |
| Lint failure on generated mocks | Regenerate mocks with `mockery`. If still failing, the cause is upstream config (`.mockery.yaml`) — STOP and ask. |
| `make precommit` fails on `go vet` | Likely an unused import or shadowed variable. Fix in the new code. |
| Tests pass locally, CI fails on coverage gate | The CI threshold may be tighter than 100% on changed files only. Check the diff lines. |
