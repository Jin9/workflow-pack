package auth

import (
	"context"
	"errors"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/common/hash"
	"gitlab.com/example-org/platform/backend/common/token"

	"gitlab.com/example-org/platform/backend/auth/app/auth/access"
	access_mocks "gitlab.com/example-org/platform/backend/auth/app/auth/access/mocks"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

type fakeSigner struct{ err error }

func (f fakeSigner) SignRS256(token.Claims) (string, error) { return "rs256.jwt", f.err }
func (f fakeSigner) SignES256(token.Claims) (string, error) { return "es256.jwt", f.err }

func testHash(t *testing.T) hash.HashManager {
	t.Helper()
	return hash.MustNewHashManager(hash.HashManagerCfgs{Pepper: "0123456789abcdef"})
}

var fixedNow = time.Date(2026, 6, 7, 12, 0, 0, 0, time.UTC)

type deps struct {
	cred  *access_mocks.CredentialStorageMock
	fam   *access_mocks.TokenFamilyStorageMock
	audit *access_mocks.AuditStorageMock
}

func newHandlerForTest(t *testing.T, signer token.JWTSigner) (*handler, deps) {
	t.Helper()
	d := deps{
		cred:  access_mocks.NewCredentialStorageMock(t),
		fam:   access_mocks.NewTokenFamilyStorageMock(t),
		audit: access_mocks.NewAuditStorageMock(t),
	}
	h := NewHandler(HandlerConfig{
		CredentialStorage:  d.cred,
		TokenFamilyStorage: d.fam,
		AuditStorage:       d.audit,
		Token:              signer,
		Hash:               testHash(t),
		Issuer:             "shoppilot",
		Audience:           "shoppilot-clients",
	})
	h.now = func() time.Time { return fixedNow }
	return h, d
}

func auditOf(eventType string) interface{} {
	return mock.MatchedBy(func(e access.AuditEvent) bool { return e.EventType == eventType })
}

func TestLogin(t *testing.T) {
	hm := testHash(t)
	const password = "correct-horse-battery"
	storedCred := access.Credential{
		EmailHash:    "ignored",
		MemberID:     "member-123",
		PasswordHash: hm.HashSha256EncodePepper(password),
	}

	t.Run("success issues a token family and audits succeeded", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(storedCred, nil)
		d.fam.EXPECT().Create(mock.Anything, mock.Anything).Return(access.TokenFamily{}, nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("auth.login.succeeded")).Return(nil)

		pair, err := h.login(context.Background(), "shopper@example.com", password)

		r.NoError(err)
		r.NotEmpty(pair.AccessToken)
		r.NotEmpty(pair.RefreshToken)
		r.Equal(int64(900), pair.ExpiresIn)
	})

	t.Run("unknown email returns generic error and audits failed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(access.Credential{}, access.ErrCredentialNotFound)
		d.audit.EXPECT().Append(mock.Anything, auditOf("auth.login.failed")).Return(nil)

		_, err := h.login(context.Background(), "nobody@example.com", password)

		r.ErrorIs(err, ErrInvalidCredentials)
	})

	t.Run("wrong password returns the same generic error and audits failed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(storedCred, nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("auth.login.failed")).Return(nil)

		_, err := h.login(context.Background(), "shopper@example.com", "wrong-password")

		r.ErrorIs(err, ErrInvalidCredentials)
	})

	t.Run("unexpected storage error is propagated, not masked as invalid credentials", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(access.Credential{}, errors.New("firestore down"))

		_, err := h.login(context.Background(), "shopper@example.com", password)

		r.Error(err)
		r.NotErrorIs(err, ErrInvalidCredentials)
	})

	t.Run("token family persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(storedCred, nil)
		d.fam.EXPECT().Create(mock.Anything, mock.Anything).Return(access.TokenFamily{}, errors.New("write failed"))

		_, err := h.login(context.Background(), "shopper@example.com", password)

		r.Error(err)
	})

	t.Run("access token signing failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{err: errors.New("sign failed")})
		d.cred.EXPECT().GetByEmailHash(mock.Anything, mock.Anything).Return(storedCred, nil)

		_, err := h.login(context.Background(), "shopper@example.com", password)

		r.Error(err)
	})
}
