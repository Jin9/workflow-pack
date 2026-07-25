package auth_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/hash"
	"gitlab.com/example-org/platform/backend/common/token"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/auth/app/auth"
	"gitlab.com/example-org/platform/backend/auth/app/auth/access"
	access_mocks "gitlab.com/example-org/platform/backend/auth/app/auth/access/mocks"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

type fakeSigner struct{}

func (fakeSigner) SignRS256(token.Claims) (string, error) { return "rs256.jwt", nil }
func (fakeSigner) SignES256(token.Claims) (string, error) { return "es256.jwt", nil }

func newHash() hash.HashManager {
	return hash.MustNewHashManager(hash.HashManagerCfgs{Pepper: "0123456789abcdef"})
}

type mockDeps struct {
	cred  *access_mocks.CredentialStorageMock
	fam   *access_mocks.TokenFamilyStorageMock
	audit *access_mocks.AuditStorageMock
}

// authAPI is the slice of the (unexported) concrete handler this external test
// exercises; *auth.handler satisfies it, letting the helper name a return type.
type authAPI interface {
	Login(*gin.Context)
	Refresh(*gin.Context)
}

func newHandler(t *testing.T) (authAPI, mockDeps) {
	t.Helper()
	d := mockDeps{
		cred:  access_mocks.NewCredentialStorageMock(t),
		fam:   access_mocks.NewTokenFamilyStorageMock(t),
		audit: access_mocks.NewAuditStorageMock(t),
	}
	h := auth.NewHandler(auth.HandlerConfig{
		CredentialStorage:  d.cred,
		TokenFamilyStorage: d.fam,
		AuditStorage:       d.audit,
		Token:              fakeSigner{},
		Hash:               newHash(),
		Issuer:             "shoppilot",
		Audience:           "shoppilot-clients",
	})
	return h, d
}

func postJSON(t *testing.T, body any) (*httptest.ResponseRecorder, *gin.Context) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	var buf bytes.Buffer
	require.NoError(t, json.NewEncoder(&buf).Encode(body))
	req := httptest.NewRequest(http.MethodPost, "http://0.0.0.0/api/v1/platform/auth/login", &buf)
	req.Header.Set("Content-Type", "application/json")
	c.Request = req
	return w, c
}

func decodeLogin(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[auth.LoginResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[auth.LoginResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func TestLoginHandler(t *testing.T) {
	const password = "correct-horse-battery"
	validCred := access.Credential{
		MemberID:     "member-123",
		PasswordHash: newHash().HashSha256EncodePepper(password),
	}

	t.Run("200 on valid credentials", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(validCred, nil)
		d.fam.EXPECT().Create(mock.Anything, mock.Anything).Return(access.TokenFamily{}, nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, auth.LoginRequest{Email: "shopper@example.com", Password: password})
		h.Login(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeLogin(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal(app.MessageSuccess, resp.Message)
	})

	t.Run("400 on missing email", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, auth.LoginRequest{Password: password})
		h.Login(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeLogin(t, w).Code)
	})

	t.Run("400 on missing password", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, auth.LoginRequest{Email: "shopper@example.com"})
		h.Login(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeLogin(t, w).Code)
	})

	t.Run("401 on invalid credentials", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(access.Credential{}, access.ErrCredentialNotFound)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, auth.LoginRequest{Email: "nobody@example.com", Password: password})
		h.Login(c)

		r.Equal(http.StatusUnauthorized, w.Code)
		r.Equal(app.CodeUnauthorized, decodeLogin(t, w).Code)
	})

	t.Run("500 on unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(access.Credential{}, errors.New("firestore down"))

		w, c := postJSON(t, auth.LoginRequest{Email: "shopper@example.com", Password: password})
		h.Login(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeLogin(t, w).Code)
	})
}
