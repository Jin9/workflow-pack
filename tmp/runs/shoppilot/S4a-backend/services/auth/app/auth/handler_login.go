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

// LoginRequest is the POST /api/v1/platform/auth/login body.
type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

// LoginResponse carries the freshly minted token pair. The gateway is responsible
// for placing the refresh token in an httpOnly cookie; the body is the contract.
type LoginResponse struct {
	AccessToken  string `json:"accessToken"`
	RefreshToken string `json:"refreshToken"`
	ExpiresIn    int64  `json:"expiresIn"`
}

// Login authenticates a member. Unknown email and wrong password are
// indistinguishable to the caller (generic 401, no enumeration).
func (h *handler) Login(c *gin.Context) {
	req, ok := wrapper.BindJSON[LoginRequest](c, slog.String("handler", "Login"))
	if !ok {
		return
	}

	ctx := c.Request.Context()

	pair, err := h.login(ctx, req.Email, req.Password)
	if err != nil {
		if errors.Is(err, ErrInvalidCredentials) {
			wrapper.Respond(c, wrapper.ResponseOption[LoginResponse]{
				HTTPStatus: http.StatusUnauthorized,
				Code:       app.CodeUnauthorized,
				Message:    app.MessageUnauthorized,
			})
			return
		}
		wrapper.Respond(c, wrapper.ResponseOption[LoginResponse]{
			HTTPStatus: http.StatusInternalServerError,
			Code:       app.CodeInternalError,
			Message:    app.MessageInternalError,
			Err:        serror.Wrap(err),
		})
		return
	}

	wrapper.Respond(c, wrapper.ResponseOption[LoginResponse]{
		HTTPStatus: http.StatusOK,
		Code:       app.CodeSuccess,
		Message:    app.MessageSuccess,
		Data: &LoginResponse{
			AccessToken:  pair.AccessToken,
			RefreshToken: pair.RefreshToken,
			ExpiresIn:    pair.ExpiresIn,
		},
	})
}
