// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"errors"
	"fmt"

	gcpfirestore "cloud.google.com/go/firestore"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ErrCredentialNotFound is returned when no credential matches the email hash.
var ErrCredentialNotFound = errors.New("credential not found")

// CredentialStorage looks up a member credential by the deterministic email hash.
type CredentialStorage interface {
	GetByEmailHash(ctx context.Context, emailHash string) (Credential, error)
}

type credentialStorage struct {
	fs *gcpfirestore.Client
}

var _ CredentialStorage = (*credentialStorage)(nil)

const credentialCollection = "credentials"

// NewCredentialStorage wires the credential repository over Firestore.
func NewCredentialStorage(fs *gcpfirestore.Client) CredentialStorage {
	return &credentialStorage{fs: fs}
}

func (s *credentialStorage) GetByEmailHash(ctx context.Context, emailHash string) (Credential, error) {
	doc, err := s.fs.Collection(credentialCollection).Doc(emailHash).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Credential{}, ErrCredentialNotFound
		}
		return Credential{}, fmt.Errorf("failed to get credential by email hash: %w", err)
	}

	var entity Credential
	if err := doc.DataTo(&entity); err != nil {
		return Credential{}, fmt.Errorf("failed to parse credential data: %w", err)
	}

	return entity, nil
}

// Credential is the stored authentication record. PasswordHash is peppered; the
// raw password and raw email are never persisted (no-enumeration is enforced at
// the service layer by returning a generic error for both lookup and compare misses).
type Credential struct {
	EmailHash    string `firestore:"email_hash" json:"emailHash"`
	MemberID     string `firestore:"member_id" json:"memberId"`
	PasswordHash string `firestore:"password_hash" json:"passwordHash"`
}
