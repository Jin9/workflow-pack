// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"errors"
	"fmt"
	"time"

	gcpfirestore "cloud.google.com/go/firestore"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ErrTokenFamilyNotFound is returned when no token family owns the presented refresh hash.
var ErrTokenFamilyNotFound = errors.New("token family not found")

// TokenFamilyStorage owns the refresh-token rotation lineage. Lookup resolves a
// family from ANY historical refresh hash (current or rotated-away) so the
// service layer can distinguish a live current token from a replayed old one.
type TokenFamilyStorage interface {
	Create(ctx context.Context, fam TokenFamily) (TokenFamily, error)
	GetByRefreshHash(ctx context.Context, refreshHash string) (TokenFamily, error)
	Rotate(ctx context.Context, familyID, newRefreshHash string, expiresAt time.Time) error
	RevokeFamily(ctx context.Context, familyID string) error
}

type tokenFamilyStorage struct {
	fs *gcpfirestore.Client
}

var _ TokenFamilyStorage = (*tokenFamilyStorage)(nil)

const (
	tokenFamilyCollection = "token_families"
	refreshIndexCollection = "refresh_hash_index"
)

// NewTokenFamilyStorage wires the token-family repository over Firestore.
func NewTokenFamilyStorage(fs *gcpfirestore.Client) TokenFamilyStorage {
	return &tokenFamilyStorage{fs: fs}
}

func (s *tokenFamilyStorage) Create(ctx context.Context, fam TokenFamily) (TokenFamily, error) {
	now := time.Now().UTC()
	fam.CreatedAt = now
	fam.UpdatedAt = now

	if _, err := s.fs.Collection(tokenFamilyCollection).Doc(fam.FamilyID).Set(ctx, fam); err != nil {
		return TokenFamily{}, fmt.Errorf("failed to create token family: %w", err)
	}
	if err := s.indexRefreshHash(ctx, fam.CurrentRefreshHash, fam.FamilyID); err != nil {
		return TokenFamily{}, err
	}
	return fam, nil
}

func (s *tokenFamilyStorage) GetByRefreshHash(ctx context.Context, refreshHash string) (TokenFamily, error) {
	idxDoc, err := s.fs.Collection(refreshIndexCollection).Doc(refreshHash).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return TokenFamily{}, ErrTokenFamilyNotFound
		}
		return TokenFamily{}, fmt.Errorf("failed to resolve refresh hash index: %w", err)
	}

	var idx refreshHashIndex
	if err := idxDoc.DataTo(&idx); err != nil {
		return TokenFamily{}, fmt.Errorf("failed to parse refresh hash index: %w", err)
	}

	famDoc, err := s.fs.Collection(tokenFamilyCollection).Doc(idx.FamilyID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return TokenFamily{}, ErrTokenFamilyNotFound
		}
		return TokenFamily{}, fmt.Errorf("failed to get token family: %w", err)
	}

	var fam TokenFamily
	if err := famDoc.DataTo(&fam); err != nil {
		return TokenFamily{}, fmt.Errorf("failed to parse token family: %w", err)
	}
	return fam, nil
}

func (s *tokenFamilyStorage) Rotate(ctx context.Context, familyID, newRefreshHash string, expiresAt time.Time) error {
	updates := []gcpfirestore.Update{
		{Path: "current_refresh_hash", Value: newRefreshHash},
		{Path: "expires_at", Value: expiresAt},
		{Path: "updated_at", Value: time.Now().UTC()},
	}
	if _, err := s.fs.Collection(tokenFamilyCollection).Doc(familyID).Update(ctx, updates); err != nil {
		return fmt.Errorf("failed to rotate token family: %w", err)
	}
	if err := s.indexRefreshHash(ctx, newRefreshHash, familyID); err != nil {
		return err
	}
	return nil
}

func (s *tokenFamilyStorage) RevokeFamily(ctx context.Context, familyID string) error {
	updates := []gcpfirestore.Update{
		{Path: "revoked", Value: true},
		{Path: "updated_at", Value: time.Now().UTC()},
	}
	if _, err := s.fs.Collection(tokenFamilyCollection).Doc(familyID).Update(ctx, updates); err != nil {
		return fmt.Errorf("failed to revoke token family: %w", err)
	}
	return nil
}

func (s *tokenFamilyStorage) indexRefreshHash(ctx context.Context, refreshHash, familyID string) error {
	if _, err := s.fs.Collection(refreshIndexCollection).Doc(refreshHash).Set(ctx, refreshHashIndex{FamilyID: familyID}); err != nil {
		return fmt.Errorf("failed to index refresh hash: %w", err)
	}
	return nil
}

type refreshHashIndex struct {
	FamilyID string `firestore:"family_id" json:"familyId"`
}

// TokenFamily is the rotation lineage for one login session. A presented refresh
// token whose hash != CurrentRefreshHash (but still resolves to the family) is a
// replay and must revoke the whole family (ADR-006 audit on every state change).
type TokenFamily struct {
	FamilyID           string    `firestore:"family_id" json:"familyId"`
	MemberID           string    `firestore:"member_id" json:"memberId"`
	CurrentRefreshHash string    `firestore:"current_refresh_hash" json:"currentRefreshHash"`
	ExpiresAt          time.Time `firestore:"expires_at" json:"expiresAt"`
	Revoked            bool      `firestore:"revoked" json:"revoked"`
	CreatedAt          time.Time `firestore:"created_at" json:"createdAt"`
	UpdatedAt          time.Time `firestore:"updated_at" json:"updatedAt"`
}
