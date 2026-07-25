package order_test

import (
	"context"
	"errors"
	"net/http"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"

	"gitlab.com/example-org/platform/backend/order/app/order"
	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func validCreateRequest() order.CreateOrderRequest {
	return order.CreateOrderRequest{
		ConfirmID: "11111111-1111-1111-1111-111111111111",
		Snapshot: order.SnapshotRequest{
			CustomerID: "member-123",
			Items: []order.OrderItemRequest{
				{SKU: "sku-1", Name: "Widget", Quantity: 1, PriceMinor: 1000},
			},
			TotalMinor: 1000,
			Address:    "1 Market St",
		},
	}
}

func TestCreateHandler(t *testing.T) {
	t.Run("200 creates a fresh order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByConfirmID(mock.Anything, mock.Anything).Return(access.Order{}, access.ErrOrderNotFound)
		d.order.EXPECT().Create(mock.Anything, mock.Anything).RunAndReturn(
			func(_ context.Context, o access.Order) (access.Order, error) { return o, nil })
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", validCreateRequest())
		h.Create(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeCreate(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal(access.OrderStateAwaitingPayment, resp.Data.State)
	})

	t.Run("200 idempotent returns existing order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		existing := access.Order{OrderNo: "order-1", ConfirmID: "11111111-1111-1111-1111-111111111111", State: access.OrderStatePaid}
		d.order.EXPECT().GetByConfirmID(mock.Anything, mock.Anything).Return(existing, nil)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", validCreateRequest())
		h.Create(c)

		r.Equal(http.StatusOK, w.Code)
		r.Equal("order-1", decodeCreate(t, w).Data.OrderNo)
	})

	t.Run("400 on missing confirmId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		req := validCreateRequest()
		req.ConfirmID = ""

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", req)
		h.Create(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCreate(t, w).Code)
	})

	t.Run("400 on confirmId not a uuid", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		req := validCreateRequest()
		req.ConfirmID = "not-a-uuid"

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", req)
		h.Create(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCreate(t, w).Code)
	})

	t.Run("400 on missing snapshot customer", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		req := validCreateRequest()
		req.Snapshot.CustomerID = ""

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", req)
		h.Create(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCreate(t, w).Code)
	})

	t.Run("500 on unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByConfirmID(mock.Anything, mock.Anything).Return(access.Order{}, errors.New("firestore down"))

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order", validCreateRequest())
		h.Create(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeCreate(t, w).Code)
	})
}
