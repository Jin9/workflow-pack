package auth

import (
	"errors"
	"log/slog"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"github.com/gin-gonic/gin"
)

// RefreshRequest is the POST /api/v1/platform/auth/refresh body.
type RefreshRequest struct {
	RefreshToken string `json:"refreshToken" binding:"required"`
}

// RefreshResponse carries the rotated token pair.
type RefreshResponse struct {
	AccessToken  string `json:"accessToken"`
	RefreshToken string `json:"refreshToken"`
	ExpiresIn    int64  `json:"expiresIn"`
}

// Refresh rotates a single-use refresh token. Replayed, expired, and unknown
// tokens all map to 401; a replay additionally revokes the token family.
func (h *handler) Refresh(c *gin.Context) {
	req, ok := wrapper.BindJSON[RefreshRequest](c, slog.String("handler", "Refresh"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	pair, err := h.refresh(ctx, req.RefreshToken)
	if err != nil {
		if errors.Is(err, ErrInvalidToken) ||
			errors.Is(err, ErrExpiredToken) ||
			errors.Is(err, ErrReplayedTokenFamilyRevoked) {
			wrapper.Respond(c, wrapper.ResponseOption[RefreshResponse]{
				HTTPStatus: http.StatusUnauthorized,
				Code:       app.CodeUnauthorized,
				Message:    app.MessageUnauthorized,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[RefreshResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[RefreshResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &RefreshResponse{
			AccessToken:  pair.AccessToken,
			RefreshToken: pair.RefreshToken,
			ExpiresIn:    pair.ExpiresIn,
		},
	})
}
