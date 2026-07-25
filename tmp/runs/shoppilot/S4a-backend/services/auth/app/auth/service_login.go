package auth

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"gitlab.com/example-org/platform/backend/common/serror"
	"gitlab.com/example-org/platform/backend/common/token"

	"gitlab.com/example-org/platform/backend/auth/app/auth/access"

	"github.com/google/uuid"
)

// ErrInvalidCredentials is the single, generic credential error. Login returns
// it for BOTH unknown-email and wrong-password to prevent account enumeration.
var ErrInvalidCredentials = errors.New("invalid credentials")

type tokenPair struct {
	AccessToken  string
	RefreshToken string
	ExpiresIn    int64
}

// login authenticates by deterministic email hash + peppered password hash, then
// mints a fresh token family. Both miss paths return ErrInvalidCredentials and
// emit auth.login.failed; success emits auth.login.succeeded (ADR-006).
func (h *handler) login(ctx context.Context, email, password string) (tokenPair, error) {
	emailHash := h.hash.HashSha256Encode(email)

	cred, err := h.credentialStorage.GetByEmailHash(ctx, emailHash)
	if err != nil {
		if errors.Is(err, access.ErrCredentialNotFound) {
			h.auditLoginFailed(ctx, emailHash)
			return tokenPair{}, ErrInvalidCredentials
		}
		return tokenPair{}, serror.Wrap(err).With(slog.String("email_hash", emailHash))
	}

	if h.hash.HashSha256EncodePepper(password) != cred.PasswordHash {
		h.auditLoginFailed(ctx, cred.MemberID)
		return tokenPair{}, ErrInvalidCredentials
	}

	pair, err := h.issueFamily(ctx, cred.MemberID)
	if err != nil {
		return tokenPair{}, serror.Wrap(err).With(slog.String("member_id", cred.MemberID))
	}

	h.audit(ctx, "auth.login.succeeded", cred.MemberID)
	return pair, nil
}

// issueFamily mints a new access JWT + opaque refresh token and persists the
// rooted token family. Shared by login and refresh-on-rotate.
func (h *handler) issueFamily(ctx context.Context, memberID string) (tokenPair, error) {
	now := h.now()
	accessToken, err := h.signAccess(memberID, now)
	if err != nil {
		return tokenPair{}, err
	}

	refreshToken := uuid.NewString()
	refreshExpiry := now.Add(refreshTokenTTL)
	fam := access.TokenFamily{
		FamilyID:           uuid.NewString(),
		MemberID:           memberID,
		CurrentRefreshHash: h.hash.HashSha256Encode(refreshToken),
		ExpiresAt:          refreshExpiry,
	}
	if _, err := h.tokenFamilyStorage.Create(ctx, fam); err != nil {
		return tokenPair{}, fmt.Errorf("failed to persist token family: %w", err)
	}

	return tokenPair{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresIn:    int64(accessTokenTTL.Seconds()),
	}, nil
}

func (h *handler) signAccess(memberID string, now time.Time) (string, error) {
	claims := token.Claims{
		Sub: memberID,
		Iss: h.issuer,
		Aud: h.audience,
		Iat: now.Unix(),
		Exp: now.Add(accessTokenTTL).Unix(),
		Jti: uuid.NewString(),
	}
	signed, err := h.token.SignES256(claims)
	if err != nil {
		return "", fmt.Errorf("failed to sign access token: %w", err)
	}
	return signed, nil
}

func (h *handler) auditLoginFailed(ctx context.Context, target string) {
	h.audit(ctx, "auth.login.failed", target)
}

func (h *handler) audit(ctx context.Context, eventType, target string) {
	ev := access.AuditEvent{
		AuditID:   uuid.NewString(),
		EventType: eventType,
		Actor:     target,
		Action:    eventType,
		Target:    target,
		Timestamp: h.now(),
	}
	if err := h.auditStorage.Append(ctx, ev); err != nil {
		slog.WarnContext(ctx, "failed to append audit event",
			slog.String("event_type", eventType), slog.String("error", err.Error()))
	}
}
