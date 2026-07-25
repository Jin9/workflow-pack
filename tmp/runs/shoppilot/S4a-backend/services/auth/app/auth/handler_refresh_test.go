package auth_test

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/auth/app/auth"
	"gitlab.com/example-org/platform/backend/auth/app/auth/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func decodeRefresh(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[auth.RefreshResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[auth.RefreshResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func TestRefreshHandler(t *testing.T) {
	const presented = "refresh-token-abc"
	currentHash := newHash().HashSha256Encode(presented)

	t.Run("200 rotates a current token", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, currentHash).Return(access.TokenFamily{
			FamilyID:           "fam-1",
			MemberID:           "member-123",
			CurrentRefreshHash: currentHash,
			ExpiresAt:          time.Now().Add(time.Hour),
		}, nil)
		d.fam.EXPECT().Rotate(mock.Anything, "fam-1", mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, auth.RefreshRequest{RefreshToken: presented})
		h.Refresh(c)

		r.Equal(http.StatusOK, w.Code)
		r.Equal(app.CodeSuccess, decodeRefresh(t, w).Code)
	})

	t.Run("400 on missing refresh token", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, auth.RefreshRequest{})
		h.Refresh(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeRefresh(t, w).Code)
	})

	t.Run("401 on unknown token", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, currentHash).Return(access.TokenFamily{}, access.ErrTokenFamilyNotFound)

		w, c := postJSON(t, auth.RefreshRequest{RefreshToken: presented})
		h.Refresh(c)

		r.Equal(http.StatusUnauthorized, w.Code)
		r.Equal(app.CodeUnauthorized, decodeRefresh(t, w).Code)
	})

	t.Run("500 on unexpected lookup error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, currentHash).Return(access.TokenFamily{}, errors.New("firestore down"))

		w, c := postJSON(t, auth.RefreshRequest{RefreshToken: presented})
		h.Refresh(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeRefresh(t, w).Code)
	})
}
