// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"fmt"
	"time"

	gcpfirestore "cloud.google.com/go/firestore"
)

// OutboxStorage is the transactional outbox (ADR-008). State changes append an
// outbox row so the event is published exactly-once by a relay; the store is
// append-only and never updated in place by the domain handler.
type OutboxStorage interface {
	Append(ctx context.Context, event OutboxEvent) error
}

type outboxStorage struct {
	fs *gcpfirestore.Client
}

var _ OutboxStorage = (*outboxStorage)(nil)

const outboxCollection = "order_outbox"

// NewOutboxStorage wires the append-only outbox repository over Firestore.
func NewOutboxStorage(fs *gcpfirestore.Client) OutboxStorage {
	return &outboxStorage{fs: fs}
}

func (s *outboxStorage) Append(ctx context.Context, event OutboxEvent) error {
	if event.CreatedAt.IsZero() {
		event.CreatedAt = time.Now().UTC()
	}
	if _, err := s.fs.Collection(outboxCollection).Doc(event.EventID).Set(ctx, event); err != nil {
		return fmt.Errorf("failed to append outbox event: %w", err)
	}
	return nil
}

// OutboxEvent is one pending domain event awaiting publication (ADR-008). The
// Payload is the serialized event body; AggregateID correlates the row to the order.
type OutboxEvent struct {
	EventID     string    `firestore:"event_id" json:"eventId"`
	EventName   string    `firestore:"event_name" json:"eventName"`
	AggregateID string    `firestore:"aggregate_id" json:"aggregateId"`
	Payload     string    `firestore:"payload" json:"payload"`
	CreatedAt   time.Time `firestore:"created_at" json:"createdAt"`
}
