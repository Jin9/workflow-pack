package order_test

import (
	"errors"
	"net/http"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func ownedOrder() access.Order {
	return access.Order{
		OrderNo: "order-1",
		State:   access.OrderStatePaid,
		Snapshot: access.Snapshot{
			CustomerID: "member-123",
			TotalMinor: 1000,
		},
	}
}

func TestGetHandler(t *testing.T) {
	t.Run("200 owner reads own order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(ownedOrder(), nil)

		w, c := newRequest(t, http.MethodGet, "/api/v1/platform/order/order-1", nil)
		c.Params = gin.Params{{Key: "orderNo", Value: "order-1"}}
		c.Request.Header.Set("X-Member-ID", "member-123")
		h.Get(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeGet(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal("order-1", resp.Data.OrderNo)
	})

	t.Run("403 when requester is not the owner", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(ownedOrder(), nil)

		w, c := newRequest(t, http.MethodGet, "/api/v1/platform/order/order-1", nil)
		c.Params = gin.Params{{Key: "orderNo", Value: "order-1"}}
		c.Request.Header.Set("X-Member-ID", "member-999")
		h.Get(c)

		r.Equal(http.StatusForbidden, w.Code)
		r.Equal(app.CodeForbidden, decodeGet(t, w).Code)
	})

	t.Run("404 on unknown order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "missing").Return(access.Order{}, access.ErrOrderNotFound)

		w, c := newRequest(t, http.MethodGet, "/api/v1/platform/order/missing", nil)
		c.Params = gin.Params{{Key: "orderNo", Value: "missing"}}
		c.Request.Header.Set("X-Member-ID", "member-123")
		h.Get(c)

		r.Equal(http.StatusNotFound, w.Code)
		r.Equal(app.CodeNotFound, decodeGet(t, w).Code)
	})

	t.Run("500 on unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(access.Order{}, errors.New("firestore down"))

		w, c := newRequest(t, http.MethodGet, "/api/v1/platform/order/order-1", nil)
		c.Params = gin.Params{{Key: "orderNo", Value: "order-1"}}
		c.Request.Header.Set("X-Member-ID", "member-123")
		h.Get(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeGet(t, w).Code)
	})
}
