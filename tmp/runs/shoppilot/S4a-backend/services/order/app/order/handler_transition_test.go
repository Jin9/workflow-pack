package order_test

import (
	"errors"
	"net/http"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"

	"gitlab.com/example-org/platform/backend/order/app/order"
	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func transitionRequest(c *gin.Context, orderNo, role string) {
	c.Params = gin.Params{{Key: "orderNo", Value: orderNo}}
	if role != "" {
		c.Request.Header.Set("X-Role", role)
	}
}

func TestTransitionHandler(t *testing.T) {
	t.Run("200 on a legal admin transition", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		paid := access.Order{OrderNo: "order-1", State: access.OrderStatePaid}
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paid, nil)
		d.order.EXPECT().UpdateState(mock.Anything, "order-1", access.OrderStatePacking, "").Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStatePacking})
		transitionRequest(c, "order-1", "admin")
		h.Transition(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeTransition(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal(access.OrderStatePacking, resp.Data.State)
	})

	t.Run("403 for a non-admin role", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStatePacking})
		transitionRequest(c, "order-1", "customer")
		h.Transition(c)

		r.Equal(http.StatusForbidden, w.Code)
		r.Equal(app.CodeForbidden, decodeTransition(t, w).Code)
	})

	t.Run("403 when the role header is absent", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStatePacking})
		transitionRequest(c, "order-1", "")
		h.Transition(c)

		r.Equal(http.StatusForbidden, w.Code)
		r.Equal(app.CodeForbidden, decodeTransition(t, w).Code)
	})

	t.Run("400 on missing targetState", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{})
		transitionRequest(c, "order-1", "admin")
		h.Transition(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeTransition(t, w).Code)
	})

	t.Run("400 on illegal backward transition", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		paid := access.Order{OrderNo: "order-1", State: access.OrderStatePaid}
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paid, nil)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStateAwaitingPayment})
		transitionRequest(c, "order-1", "admin")
		h.Transition(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeTransition(t, w).Code)
	})

	t.Run("400 when shipping without a tracking number", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		packing := access.Order{OrderNo: "order-1", State: access.OrderStatePacking}
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(packing, nil)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStateShipped})
		transitionRequest(c, "order-1", "admin")
		h.Transition(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeTransition(t, w).Code)
	})

	t.Run("404 on unknown order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "missing").Return(access.Order{}, access.ErrOrderNotFound)

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/missing/transition",
			order.TransitionRequest{TargetState: access.OrderStatePacking})
		transitionRequest(c, "missing", "admin")
		h.Transition(c)

		r.Equal(http.StatusNotFound, w.Code)
		r.Equal(app.CodeNotFound, decodeTransition(t, w).Code)
	})

	t.Run("500 on unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(access.Order{}, errors.New("firestore down"))

		w, c := newRequest(t, http.MethodPost, "/api/v1/platform/order/order-1/transition",
			order.TransitionRequest{TargetState: access.OrderStatePacking})
		transitionRequest(c, "order-1", "admin")
		h.Transition(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeTransition(t, w).Code)
	})
}
