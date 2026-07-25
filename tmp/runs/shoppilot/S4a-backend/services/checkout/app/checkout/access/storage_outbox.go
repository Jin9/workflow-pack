// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"fmt"
	"time"

	gcpfirestore "cloud.google.com/go/firestore"
)

// OutboxStorage is the transactional outbox (ADR-008). Domain events are appended
// here in the same logical unit as the state change; a separate relay publishes
// them to Kafka, so the service layer never produces directly.
type OutboxStorage interface {
	Append(ctx context.Context, event OutboxEvent) error
}

type outboxStorage struct {
	fs *gcpfirestore.Client
}

var _ OutboxStorage = (*outboxStorage)(nil)

const outboxCollection = "checkout_outbox"

// NewOutboxStorage wires the transactional outbox over Firestore.
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

// OutboxEvent is one pending domain event awaiting relay to the message bus.
// Payload is the JSON-serialized event body; no PAN/CVV is ever placed in it.
type OutboxEvent struct {
	EventID    string    `firestore:"event_id" json:"eventId"`
	EventType  string    `firestore:"event_type" json:"eventType"`
	AggregateID string   `firestore:"aggregate_id" json:"aggregateId"`
	Payload    string    `firestore:"payload" json:"payload"`
	CreatedAt  time.Time `firestore:"created_at" json:"createdAt"`
}
