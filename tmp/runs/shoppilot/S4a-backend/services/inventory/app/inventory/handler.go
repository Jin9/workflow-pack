package inventory

import (
	"context"
	"log/slog"
	"time"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/google/uuid"
)

// reservationTTL is the window a reservation holds stock before it is eligible
// for compensation (ADR-004: release is the rollback, not a stock mutation undo).
const reservationTTL = 30 * time.Minute

// HandlerConfig is the dependency set for the inventory domain, wired from the
// composition root (router/deps.go) in router/router.go's registerInventoryRoutes
// and router/subscriber.go's registerInventoryEvents.
type HandlerConfig struct {
	StockStorage       access.StockStorage
	ReservationStorage access.ReservationStorage
	AuditStorage       access.AuditStorage
}

type handler struct {
	stockStorage       access.StockStorage
	reservationStorage access.ReservationStorage
	auditStorage       access.AuditStorage
	now                func() time.Time
}

// NewHandler builds the inventory domain handler from its dependencies.
func NewHandler(cfg HandlerConfig) *handler {
	return &handler{
		stockStorage:       cfg.StockStorage,
		reservationStorage: cfg.ReservationStorage,
		auditStorage:       cfg.AuditStorage,
		now:                func() time.Time { return time.Now().UTC() },
	}
}

// audit appends one append-only audit event (ADR-006). A failure to persist the
// audit record is logged but never fails the business operation.
func (h *handler) audit(ctx context.Context, eventType, target string) {
	ev := access.AuditEvent{
		AuditID:   uuid.NewString(),
		EventType: eventType,
		Actor:     "system",
		Action:    eventType,
		Target:    target,
		Timestamp: h.now(),
	}
	if err := h.auditStorage.Append(ctx, ev); err != nil {
		slog.WarnContext(ctx, "failed to append audit event",
			slog.String("event_type", eventType), slog.String("error", err.Error()))
	}
}
