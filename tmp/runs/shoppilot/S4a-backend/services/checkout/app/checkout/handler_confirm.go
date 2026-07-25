package checkout

import (
	"errors"
	"log/slog"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"github.com/gin-gonic/gin"
)

// ConfirmRequest is the POST /api/v1/platform/checkout/confirm body. The total is
// deliberately absent: the server computes it and never trusts a client figure.
type ConfirmRequest struct {
	CartID         string `json:"cartId" binding:"required"`
	Address        string `json:"address" binding:"required"`
	Coupon         string `json:"coupon"`
	IdempotencyKey string `json:"idempotencyKey" binding:"required,uuid"`
}

// ConfirmResponse carries the created order and its server-computed total.
type ConfirmResponse struct {
	OrderID    string `json:"orderId"`
	TotalMinor int    `json:"totalMinor"`
}

// Confirm orchestrates a checkout: idempotency replay, server-side total compute,
// coupon re-validation, sync reserve→create-order, outbox append, and audit.
// Replays are returned verbatim; domain failures map to 400; auth gaps to 401.
func (h *handler) Confirm(c *gin.Context) {
	req, ok := wrapper.BindJSON[ConfirmRequest](c, slog.String("handler", "Confirm"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	result, err := h.confirm(ctx, *req)
	if err != nil {
		if errors.Is(err, ErrCouponExpired) || errors.Is(err, ErrOutOfStock) {
			wrapper.Respond(c, wrapper.ResponseOption[ConfirmResponse]{
				HTTPStatus: http.StatusBadRequest,
				Code:       app.CodeBadRequest,
				Message:    app.MessageBadRequest,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[ConfirmResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[ConfirmResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &ConfirmResponse{
			OrderID:    result.OrderID,
			TotalMinor: result.TotalMinor,
		},
	})
}
