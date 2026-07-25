package auth

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/auth/app/auth/access"

	"github.com/google/uuid"
)

var (
	// ErrInvalidToken is returned when the refresh token resolves to no family.
	ErrInvalidToken = errors.New("invalid refresh token")
	// ErrExpiredToken is returned when the family's refresh window has elapsed.
	ErrExpiredToken = errors.New("expired refresh token")
	// ErrReplayedTokenFamilyRevoked is returned when an already-rotated (or
	// already-revoked) refresh token is presented; the whole family is revoked.
	ErrReplayedTokenFamilyRevoked = errors.New("refresh token replayed; family revoked")
)

// refresh performs single-use rotation. A token whose hash is the family's
// CURRENT hash rotates to a fresh pair; an OLD hash that still resolves to a live
// family is a replay → revoke the family (auth.token.family_revoked). Expiry and
// unknown tokens are rejected without rotation.
func (h *handler) refresh(ctx context.Context, refreshToken string) (tokenPair, error) {
	presentedHash := h.hash.HashSha256Encode(refreshToken)

	fam, err := h.tokenFamilyStorage.GetByRefreshHash(ctx, presentedHash)
	if err != nil {
		if errors.Is(err, access.ErrTokenFamilyNotFound) {
			return tokenPair{}, ErrInvalidToken
		}
		return tokenPair{}, serror.Wrap(err)
	}

	if fam.Revoked {
		return tokenPair{}, ErrReplayedTokenFamilyRevoked
	}

	if fam.CurrentRefreshHash != presentedHash {
		if err := h.tokenFamilyStorage.RevokeFamily(ctx, fam.FamilyID); err != nil {
			return tokenPair{}, serror.Wrap(err).With(slog.String("family_id", fam.FamilyID))
		}
		h.audit(ctx, "auth.token.family_revoked", fam.MemberID)
		return tokenPair{}, ErrReplayedTokenFamilyRevoked
	}

	if h.now().After(fam.ExpiresAt) {
		return tokenPair{}, ErrExpiredToken
	}

	pair, err := h.rotateFamily(ctx, fam)
	if err != nil {
		return tokenPair{}, serror.Wrap(err).With(slog.String("family_id", fam.FamilyID))
	}

	h.audit(ctx, "auth.token.refreshed", fam.MemberID)
	return pair, nil
}

func (h *handler) rotateFamily(ctx context.Context, fam access.TokenFamily) (tokenPair, error) {
	now := h.now()
	accessToken, err := h.signAccess(fam.MemberID, now)
	if err != nil {
		return tokenPair{}, err
	}

	newRefresh := uuid.NewString()
	newExpiry := now.Add(refreshTokenTTL)
	if err := h.tokenFamilyStorage.Rotate(ctx, fam.FamilyID, h.hash.HashSha256Encode(newRefresh), newExpiry); err != nil {
		return tokenPair{}, fmt.Errorf("failed to rotate token family: %w", err)
	}

	return tokenPair{
		AccessToken:  accessToken,
		RefreshToken: newRefresh,
		ExpiresIn:    int64(accessTokenTTL.Seconds()),
	}, nil
}
