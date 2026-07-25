package order

import (
	"errors"
	"log/slog"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"github.com/gin-gonic/gin"
)

// TransitionRequest is the POST /api/v1/platform/order/:orderNo/transition body (admin).
type TransitionRequest struct {
	TargetState string `json:"targetState" binding:"required"`
	TrackingNo  string `json:"trackingNo"`
}

// TransitionResponse echoes the order's new state after a successful transition.
type TransitionResponse struct {
	OrderNo    string `json:"orderNo"`
	State      string `json:"state"`
	TrackingNo string `json:"trackingNo,omitempty"`
}

// Transition advances an order through the forward-only state machine. It is an
// admin-only operation: the caller role is read from the X-Role header and must
// be "admin", otherwise 403. Backward/illegal transitions and a missing tracking
// number on "shipped" are 400.
func (h *handler) Transition(c *gin.Context) {
	if c.GetHeader("X-Role") != roleAdmin {
		wrapper.Respond(c, wrapper.ResponseOption[TransitionResponse]{
			HTTPStatus: http.StatusForbidden,
			Code:       app.CodeForbidden,
			Message:    app.MessageForbidden,
		})
		return
	}

	req, ok := wrapper.BindJSON[TransitionRequest](c, slog.String("handler", "Transition"))
	if !ok {
		return
	}

	orderNo := c.Param("orderNo")
	ctx := c.Request.Context()

	order, err := h.transition(ctx, orderNo, req.TargetState, req.TrackingNo)
	if err != nil {
		switch {
		case errors.Is(err, ErrNotFound):
			wrapper.Respond(c, wrapper.ResponseOption[TransitionResponse]{
				HTTPStatus: http.StatusNotFound,
				Code:       app.CodeNotFound,
				Message:    app.MessageNotFound,
			})
		case errors.Is(err, ErrIllegalBackward), errors.Is(err, ErrMissingTrackingOnShipped):
			wrapper.Respond(c, wrapper.ResponseOption[TransitionResponse]{
				HTTPStatus: http.StatusBadRequest,
				Code:       app.CodeBadRequest,
				Message:    app.MessageBadRequest,
				Err:        serror.Wrap(err),
			})
		default:
			wrapper.Respond(c, wrapper.ResponseOption[TransitionResponse]{
				HTTPStatus: http.StatusInternalServerError,
				Code:       app.CodeInternalError,
				Message:    app.MessageInternalError,
				Err:        serror.Wrap(err),
			})
		}
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[TransitionResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &TransitionResponse{
			OrderNo:    order.OrderNo,
			State:      order.State,
			TrackingNo: order.TrackingNo,
		},
	})
}
