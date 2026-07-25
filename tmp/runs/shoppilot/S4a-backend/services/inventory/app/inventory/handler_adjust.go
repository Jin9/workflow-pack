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

// AdjustRequest is the POST /api/v1/platform/inventory/adjust body (admin). The
// newAvailable is an absolute count, not a delta. Pointer-required so an
// explicit 0 is honoured rather than rejected as the zero value.
type AdjustRequest struct {
	SKU          string `json:"sku" binding:"required"`
	NewAvailable *int   `json:"newAvailable" binding:"required"`
	Reason       string `json:"reason" binding:"required"`
}

// AdjustResponse echoes the post-adjustment available count.
type AdjustResponse struct {
	SKU          string `json:"sku"`
	NewAvailable int    `json:"newAvailable"`
}

// Adjust sets a SKU's absolute available count (manual stock correction).
// Unknown SKU maps to 404; an available below the reserved hold maps to 400.
func (h *handler) Adjust(c *gin.Context) {
	req, ok := wrapper.BindJSON[AdjustRequest](c, slog.String("handler", "Adjust"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	if err := h.adjust(ctx, req.SKU, *req.NewAvailable, req.Reason); err != nil {
		switch {
		case errors.Is(err, access.ErrBelowReserved):
			wrapper.Respond(c, wrapper.ResponseOption[AdjustResponse]{
				HTTPStatus: http.StatusBadRequest,
				Code:       app.CodeBadRequest,
				Message:    app.MessageBadRequest,
			})
			return
		case errors.Is(err, access.ErrSKUNotFound):
			wrapper.Respond(c, wrapper.ResponseOption[AdjustResponse]{
				HTTPStatus: http.StatusNotFound,
				Code:       app.CodeNotFound,
				Message:    app.MessageNotFound,
			})
			return
		default:
			wrapper.Respond(c, wrapper.ResponseOption[AdjustResponse]{
				HTTPStatus: http.StatusInternalServerError,
				Code:       app.CodeInternalError,
				Message:    app.MessageInternalError,
				Err:        serror.Wrap(err).With(slog.String("sku", req.SKU)),
			})
			return
		}
	}

	wrapper.Respond(c, wrapper.ResponseOption[AdjustResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &AdjustResponse{
			SKU:          req.SKU,
			NewAvailable: *req.NewAvailable,
		},
	})
}
