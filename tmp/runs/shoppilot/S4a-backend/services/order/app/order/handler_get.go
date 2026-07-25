package order

import (
	"errors"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"github.com/gin-gonic/gin"
)

// GetOrderResponse is the customer-facing view of an order: its snapshot + status.
type GetOrderResponse struct {
	OrderNo    string          `json:"orderNo"`
	State      string          `json:"state"`
	TrackingNo string          `json:"trackingNo,omitempty"`
	Snapshot   SnapshotPayload `json:"snapshot"`
}

// Get returns one order to its owner only. The caller identity is read from the
// X-Member-ID header (set by the gateway); a mismatch is reported as 403, and an
// unknown order as 404.
func (h *handler) Get(c *gin.Context) {
	orderNo := c.Param("orderNo")
	memberID := c.GetHeader("X-Member-ID")

	ctx := c.Request.Context()

	order, err := h.get(ctx, orderNo, memberID)
	if err != nil {
		if errors.Is(err, ErrNotFound) {
			wrapper.Respond(c, wrapper.ResponseOption[GetOrderResponse]{
				HTTPStatus: http.StatusNotFound,
				Code:       app.CodeNotFound,
				Message:    app.MessageNotFound,
			})
			return
		}
		if errors.Is(err, ErrNotOwner) {
			wrapper.Respond(c, wrapper.ResponseOption[GetOrderResponse]{
				HTTPStatus: http.StatusForbidden,
				Code:       app.CodeForbidden,
				Message:    app.MessageForbidden,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[GetOrderResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[GetOrderResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &GetOrderResponse{
			OrderNo:    order.OrderNo,
			State:      order.State,
			TrackingNo: order.TrackingNo,
			Snapshot:   toSnapshotPayload(order.Snapshot),
		},
	})
}
