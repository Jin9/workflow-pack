# S3 FE state binding — checkout context

Per operation, the FE binds four UI states (loading / empty / error / optimistic). Money paths (confirm/capture) are **never** optimistic. Errors map each `failure_mode` to a microcopy key.

- loading: skeleton on first fetch
- empty: typed empty-state copy
- error: failure_mode -> `microcopy.json` key
- optimistic: cart mutations only
