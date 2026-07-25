package auth

import (
	"context"
	"errors"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/auth/app/auth/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func TestRefresh(t *testing.T) {
	hm := testHash(t)
	const presented = "refresh-token-abc"
	presentedHash := hm.HashSha256Encode(presented)

	liveFamily := func() access.TokenFamily {
		return access.TokenFamily{
			FamilyID:           "fam-1",
			MemberID:           "member-123",
			CurrentRefreshHash: presentedHash,
			ExpiresAt:          fixedNow.Add(time.Hour),
		}
	}

	t.Run("current token rotates and audits refreshed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(liveFamily(), nil)
		d.fam.EXPECT().Rotate(mock.Anything, "fam-1", mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("auth.token.refreshed")).Return(nil)

		pair, err := h.refresh(context.Background(), presented)

		r.NoError(err)
		r.NotEmpty(pair.AccessToken)
		r.NotEmpty(pair.RefreshToken)
		r.NotEqual(presented, pair.RefreshToken)
	})

	t.Run("unknown token is invalid", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(access.TokenFamily{}, access.ErrTokenFamilyNotFound)

		_, err := h.refresh(context.Background(), presented)

		r.ErrorIs(err, ErrInvalidToken)
	})

	t.Run("replayed old token revokes the family and audits", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		stale := liveFamily()
		stale.CurrentRefreshHash = "a-newer-hash" // presented hash is an older, rotated-away token
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(stale, nil)
		d.fam.EXPECT().RevokeFamily(mock.Anything, "fam-1").Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("auth.token.family_revoked")).Return(nil)

		_, err := h.refresh(context.Background(), presented)

		r.ErrorIs(err, ErrReplayedTokenFamilyRevoked)
	})

	t.Run("already-revoked family rejects without re-revoking", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		revoked := liveFamily()
		revoked.Revoked = true
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(revoked, nil)

		_, err := h.refresh(context.Background(), presented)

		r.ErrorIs(err, ErrReplayedTokenFamilyRevoked)
	})

	t.Run("expired family is rejected", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		expired := liveFamily()
		expired.ExpiresAt = fixedNow.Add(-time.Hour)
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(expired, nil)

		_, err := h.refresh(context.Background(), presented)

		r.ErrorIs(err, ErrExpiredToken)
	})

	t.Run("unexpected lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(access.TokenFamily{}, errors.New("firestore down"))

		_, err := h.refresh(context.Background(), presented)

		r.Error(err)
		r.NotErrorIs(err, ErrInvalidToken)
	})

	t.Run("rotation persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t, fakeSigner{})
		d.fam.EXPECT().GetByRefreshHash(mock.Anything, presentedHash).Return(liveFamily(), nil)
		d.fam.EXPECT().Rotate(mock.Anything, "fam-1", mock.Anything, mock.Anything).Return(errors.New("write failed"))

		_, err := h.refresh(context.Background(), presented)

		r.Error(err)
	})
}
