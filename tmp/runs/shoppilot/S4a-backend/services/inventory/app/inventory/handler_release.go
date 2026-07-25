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

// ReleaseRequest is the POST /api/v1/platform/inventory/release body. This is
// the compensation / TTL-expiry target: it returns held stock to available.
type ReleaseRequest struct {
	ReservationID string `json:"reservationId" binding:"required,uuid"`
	Reason        string `json:"reason" binding:"required"`
}

// ReleaseResponse confirms the reservation is released (or already was).
type ReleaseResponse struct {
	ReservationID string `json:"reservationId"`
	Status        string `json:"status"`
}

// Release frees a reservation's held stock. Unknown reservation maps to 404;
// releasing an already-released reservation is a no-op success (idempotent).
func (h *handler) Release(c *gin.Context) {
	req, ok := wrapper.BindJSON[ReleaseRequest](c, slog.String("handler", "Release"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	if err := h.release(ctx, req.ReservationID, req.Reason); err != nil {
		if errors.Is(err, access.ErrReservationNotFound) {
			wrapper.Respond(c, wrapper.ResponseOption[ReleaseResponse]{
				HTTPStatus: http.StatusNotFound,
				Code:       app.CodeNotFound,
				Message:    app.MessageNotFound,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[ReleaseResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err).With(slog.String("reservation_id", req.ReservationID)),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[ReleaseResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &ReleaseResponse{
			ReservationID: req.ReservationID,
			Status:        access.ReservationStatusReleased,
		},
	})
}
