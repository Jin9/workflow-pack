// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"fmt"
	"time"

	gcpfirestore "cloud.google.com/go/firestore"
)

// AuditStorage is the append-only audit trail (ADR-006). Every state-changing
// path emits exactly one event; the store is never updated or deleted.
type AuditStorage interface {
	Append(ctx context.Context, event AuditEvent) error
}

type auditStorage struct {
	fs *gcpfirestore.Client
}

var _ AuditStorage = (*auditStorage)(nil)

const auditCollection = "audit_events"

// NewAuditStorage wires the append-only audit repository over Firestore.
func NewAuditStorage(fs *gcpfirestore.Client) AuditStorage {
	return &auditStorage{fs: fs}
}

func (s *auditStorage) Append(ctx context.Context, event AuditEvent) error {
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now().UTC()
	}
	if _, _, err := s.fs.Collection(auditCollection).Add(ctx, event); err != nil {
		return fmt.Errorf("failed to append audit event: %w", err)
	}
	return nil
}

// AuditEvent is one append-only audit record. AuditID correlates a record's
// events end-to-end; no PII/token/PAN is ever placed in the event.
type AuditEvent struct {
	AuditID   string    `firestore:"audit_id" json:"auditId"`
	EventType string    `firestore:"event_type" json:"eventType"`
	Actor     string    `firestore:"actor" json:"actor"`
	Action    string    `firestore:"action" json:"action"`
	Target    string    `firestore:"target" json:"target"`
	Timestamp time.Time `firestore:"timestamp" json:"timestamp"`
}
