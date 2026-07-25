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

// ErrIdempotencyNotFound is returned when no record matches the idempotency key.
var ErrIdempotencyNotFound = errors.New("idempotency record not found")

// IdempotencyStorage is the replay-safety ledger (ADR A2). A successful confirm
// stores its full response keyed by the client idempotency key; a re-submission
// with the same key returns the stored response instead of re-running the flow.
type IdempotencyStorage interface {
	GetByKey(ctx context.Context, key string) (IdempotencyRecord, error)
	Save(ctx context.Context, record IdempotencyRecord) error
}

type idempotencyStorage struct {
	fs *gcpfirestore.Client
}

var _ IdempotencyStorage = (*idempotencyStorage)(nil)

const idempotencyCollection = "checkout_idempotency"

// NewIdempotencyStorage wires the idempotency ledger over Firestore.
func NewIdempotencyStorage(fs *gcpfirestore.Client) IdempotencyStorage {
	return &idempotencyStorage{fs: fs}
}

func (s *idempotencyStorage) GetByKey(ctx context.Context, key string) (IdempotencyRecord, error) {
	doc, err := s.fs.Collection(idempotencyCollection).Doc(key).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return IdempotencyRecord{}, ErrIdempotencyNotFound
		}
		return IdempotencyRecord{}, fmt.Errorf("failed to get idempotency record: %w", err)
	}

	var entity IdempotencyRecord
	if err := doc.DataTo(&entity); err != nil {
		return IdempotencyRecord{}, fmt.Errorf("failed to parse idempotency record: %w", err)
	}
	return entity, nil
}

func (s *idempotencyStorage) Save(ctx context.Context, record IdempotencyRecord) error {
	if record.CreatedAt.IsZero() {
		record.CreatedAt = time.Now().UTC()
	}
	if _, err := s.fs.Collection(idempotencyCollection).Doc(record.Key).Set(ctx, record); err != nil {
		return fmt.Errorf("failed to save idempotency record: %w", err)
	}
	return nil
}

// IdempotencyRecord is one stored confirm outcome. Response is the JSON-serialized
// confirm response replayed verbatim on a same-key re-submission; no PII/PAN is stored.
type IdempotencyRecord struct {
	Key        string    `firestore:"key" json:"key"`
	OrderID    string    `firestore:"order_id" json:"orderId"`
	TotalMinor int       `firestore:"total_minor" json:"totalMinor"`
	Response   string    `firestore:"response" json:"response"`
	CreatedAt  time.Time `firestore:"created_at" json:"createdAt"`
}
