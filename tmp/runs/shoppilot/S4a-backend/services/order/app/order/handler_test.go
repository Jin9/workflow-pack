package order_test

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"

	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/order/app/order"
	access_mocks "gitlab.com/example-org/platform/backend/order/app/order/access/mocks"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/require"
)

// orderAPI is the slice of the (unexported) concrete handler this external test
// exercises; *order.handler satisfies it, letting the helper name a return type.
type orderAPI interface {
	Create(*gin.Context)
	Get(*gin.Context)
	Transition(*gin.Context)
}

type mockDeps struct {
	order  *access_mocks.OrderStorageMock
	outbox *access_mocks.OutboxStorageMock
	audit  *access_mocks.AuditStorageMock
}

func newHandler(t *testing.T) (orderAPI, mockDeps) {
	t.Helper()
	d := mockDeps{
		order:  access_mocks.NewOrderStorageMock(t),
		outbox: access_mocks.NewOutboxStorageMock(t),
		audit:  access_mocks.NewAuditStorageMock(t),
	}
	h := order.NewHandler(order.HandlerConfig{
		OrderStorage:  d.order,
		OutboxStorage: d.outbox,
		AuditStorage:  d.audit,
	})
	return h, d
}

// newRequest builds a gin test context for the given method/target with an
// optional JSON body. Path params and headers are set by the caller on the
// returned context/request.
func newRequest(t *testing.T, method, target string, body any) (*httptest.ResponseRecorder, *gin.Context) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	var rdr *bytes.Buffer
	if body != nil {
		rdr = &bytes.Buffer{}
		require.NoError(t, json.NewEncoder(rdr).Encode(body))
	} else {
		rdr = &bytes.Buffer{}
	}
	req := httptest.NewRequest(method, "http://0.0.0.0"+target, rdr)
	req.Header.Set("Content-Type", "application/json")
	c.Request = req
	return w, c
}

func decodeCreate(t *testing.T, w *httptest.ResponseRecorder) wrapper.Response[order.CreateOrderResponse] {
	t.Helper()
	var resp wrapper.Response[order.CreateOrderResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func decodeGet(t *testing.T, w *httptest.ResponseRecorder) wrapper.Response[order.GetOrderResponse] {
	t.Helper()
	var resp wrapper.Response[order.GetOrderResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func decodeTransition(t *testing.T, w *httptest.ResponseRecorder) wrapper.Response[order.TransitionResponse] {
	t.Helper()
	var resp wrapper.Response[order.TransitionResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}
