package inventory

import (
	"errors"
	"log/slog"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/gin-gonic/gin"
)

// ReserveItem is one SKU/quantity line in a reserve request.
type ReserveItem struct {
	SKU string `json:"sku" binding:"required"`
	Qty int    `json:"qty" binding:"required,gt=0"`
}

// ReserveRequest is the POST /api/v1/platform/inventory/reserve body. The
// confirmId is the idempotency key: a repeated confirmId returns the existing
// reservation without decrementing stock a second time.
type ReserveRequest struct {
	ConfirmID string        `json:"confirmId" binding:"required,uuid"`
	Items     []ReserveItem `json:"items" binding:"required,min=1,dive"`
}

// ReserveResponse carries the reservation handle and its TTL deadline.
type ReserveResponse struct {
	ReservationID string `json:"reservationId"`
	ExpiresAt     string `json:"expiresAt"`
}

// Reserve holds stock for an in-flight order. Out-of-stock maps to 400, an
// unknown SKU to 404; idempotent on confirmId.
func (h *handler) Reserve(c *gin.Context) {
	req, ok := wrapper.BindJSON[ReserveRequest](c, slog.String("handler", "Reserve"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	reservation, err := h.reserve(ctx, req.ConfirmID, req.Items)
	if err != nil {
		switch {
		case errors.Is(err, access.ErrInsufficientStock):
			wrapper.Respond(c, wrapper.ResponseOption[ReserveResponse]{
				HTTPStatus: http.StatusBadRequest,
				Code:       app.CodeBadRequest,
				Message:    app.MessageBadRequest,
			})
			return
		case errors.Is(err, access.ErrSKUNotFound):
			wrapper.Respond(c, wrapper.ResponseOption[ReserveResponse]{
				HTTPStatus: http.StatusNotFound,
				Code:       app.CodeNotFound,
				Message:    app.MessageNotFound,
			})
			return
		default:
			wrapper.Respond(c, wrapper.ResponseOption[ReserveResponse]{
				HTTPStatus: http.StatusInternalServerError,
				Code:       app.CodeInternalError,
				Message:    app.MessageInternalError,
				Err:        serror.Wrap(err).With(slog.String("confirm_id", req.ConfirmID)),
			})
			return
		}
	}

	wrapper.Respond(c, wrapper.ResponseOption[ReserveResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &ReserveResponse{
			ReservationID: reservation.ReservationID,
			ExpiresAt:     reservation.ExpiresAt.Format(timeLayout),
		},
	})
}
