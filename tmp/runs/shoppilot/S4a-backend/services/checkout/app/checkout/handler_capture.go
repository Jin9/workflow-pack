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

// CaptureRequest is the POST /api/v1/platform/checkout/capture body. Amount is the
// claimed capture amount; it is validated against the server-recorded order total.
type CaptureRequest struct {
	OrderID         string `json:"orderId" binding:"required,uuid"`
	ProviderEventID string `json:"providerEventId" binding:"required"`
	Amount          int    `json:"amount" binding:"required"`
}

// CaptureResponse reports the capture outcome for the order.
type CaptureResponse struct {
	OrderID     string `json:"orderId"`
	AmountMinor int    `json:"amountMinor"`
	Captured    bool   `json:"captured"`
}

// Capture settles an authorized payment. It is deduped on the provider event ID
// (replay returns the prior outcome), rejects an amount that disagrees with the
// server total, and maps PSP failures: declined/amount-mismatch → 400, timeout → 503.
func (h *handler) Capture(c *gin.Context) {
	req, ok := wrapper.BindJSON[CaptureRequest](c, slog.String("handler", "Capture"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	result, err := h.capture(ctx, *req)
	if err != nil {
		if errors.Is(err, ErrPaymentTimeout) {
			wrapper.Respond(c, wrapper.ResponseOption[CaptureResponse]{
				HTTPStatus: http.StatusServiceUnavailable,
				Code:       app.CodeServiceUnavail,
				Message:    app.MessageServiceUnavail,
			})
			return
		}
		if errors.Is(err, ErrPaymentDeclined) || errors.Is(err, ErrAmountMismatch) {
			wrapper.Respond(c, wrapper.ResponseOption[CaptureResponse]{
				HTTPStatus: http.StatusBadRequest,
				Code:       app.CodeBadRequest,
				Message:    app.MessageBadRequest,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[CaptureResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[CaptureResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &CaptureResponse{
			OrderID:     result.OrderID,
			AmountMinor: result.AmountMinor,
			Captured:    result.Captured,
		},
	})
}
