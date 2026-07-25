package order

import (
	"context"
	"log/slog"
	"time"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/google/uuid"
)

// Audit event types emitted by the order domain (ADR-006).
const (
	eventOrderConfirmed     = "order.confirmed"
	eventPaymentCaptured    = "order.payment.captured"
	eventOrderStatusChanged = "order.status.changed"
)

// HandlerConfig is the dependency set for the order domain, wired from the
// composition root (router/deps.go) in router/router.go's registerOrderRoutes.
type HandlerConfig struct {
	OrderStorage  access.OrderStorage
	OutboxStorage access.OutboxStorage
	AuditStorage  access.AuditStorage
}

type handler struct {
	orderStorage  access.OrderStorage
	outboxStorage access.OutboxStorage
	auditStorage  access.AuditStorage
	now           func() time.Time
}

// NewHandler builds the order domain handler from its dependencies.
func NewHandler(cfg HandlerConfig) *handler {
	return &handler{
		orderStorage:  cfg.OrderStorage,
		outboxStorage: cfg.OutboxStorage,
		auditStorage:  cfg.AuditStorage,
		now:           func() time.Time { return time.Now().UTC() },
	}
}

// audit appends one audit event (ADR-006). A failure to persist the audit row is
// logged and swallowed so it never masks the primary domain outcome.
func (h *handler) audit(ctx context.Context, eventType, actor, target string) {
	ev := access.AuditEvent{
		AuditID:   uuid.NewString(),
		EventType: eventType,
		Actor:     actor,
		Action:    eventType,
		Target:    target,
		Timestamp: h.now(),
	}
	if err := h.auditStorage.Append(ctx, ev); err != nil {
		slog.WarnContext(ctx, "failed to append audit event",
			slog.String("event_type", eventType), slog.String("error", err.Error()))
	}
}
