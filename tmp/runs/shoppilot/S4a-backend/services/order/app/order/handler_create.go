package order

import (
	"log/slog"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"github.com/gin-gonic/gin"
)

// SnapshotRequest is the immutable order snapshot supplied at confirmation (ADR-003).
type SnapshotRequest struct {
	CustomerID string             `json:"customerId" binding:"required"`
	Items      []OrderItemRequest `json:"items" binding:"required,min=1,dive"`
	TotalMinor int                `json:"totalMinor" binding:"required"`
	Address    string             `json:"address" binding:"required"`
}

// OrderItemRequest is one confirmed line item.
type OrderItemRequest struct {
	SKU        string `json:"sku" binding:"required"`
	Name       string `json:"name" binding:"required"`
	Quantity   int    `json:"quantity" binding:"required"`
	PriceMinor int    `json:"priceMinor" binding:"required"`
}

// CreateOrderRequest is the POST /api/v1/platform/order body (system_internal).
type CreateOrderRequest struct {
	ConfirmID string          `json:"confirmId" binding:"required,uuid"`
	Snapshot  SnapshotRequest `json:"snapshot" binding:"required"`
}

// CreateOrderResponse echoes the created (or idempotently re-returned) order.
type CreateOrderResponse struct {
	OrderNo   string          `json:"orderNo"`
	State     string          `json:"state"`
	ConfirmID string          `json:"confirmId"`
	Snapshot  SnapshotPayload `json:"snapshot"`
}

// SnapshotPayload is the snapshot as returned on the wire.
type SnapshotPayload struct {
	CustomerID string             `json:"customerId"`
	Items      []OrderItemPayload `json:"items"`
	TotalMinor int                `json:"totalMinor"`
	Address    string             `json:"address"`
}

// OrderItemPayload is one snapshot line item as returned on the wire.
type OrderItemPayload struct {
	SKU        string `json:"sku"`
	Name       string `json:"name"`
	Quantity   int    `json:"quantity"`
	PriceMinor int    `json:"priceMinor"`
}

// Create confirms an order. It is idempotent on confirmId: a repeat call returns
// the existing order instead of creating a duplicate. The snapshot is frozen at
// this point and never mutated thereafter (ADR-003).
func (h *handler) Create(c *gin.Context) {
	req, ok := wrapper.BindJSON[CreateOrderRequest](c, slog.String("handler", "Create"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	order, err := h.create(ctx, *req)
	if err != nil {
		wrapper.Respond(c, wrapper.ResponseOption[CreateOrderResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[CreateOrderResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data:       toCreateResponse(order),
	})
}
