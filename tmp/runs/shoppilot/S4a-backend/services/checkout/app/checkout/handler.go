package checkout

import (
	"context"
	"log/slog"
	"time"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/google/uuid"
)

// HandlerConfig is the dependency set for the checkout domain, wired from the
// composition root (router/deps.go) in router/router.go's registerCheckoutRoutes.
type HandlerConfig struct {
	CartStorage        access.CartStorage
	IdempotencyStorage access.IdempotencyStorage
	CouponStorage      access.CouponStorage
	CaptureStorage     access.CaptureStorage
	OutboxStorage      access.OutboxStorage
	AuditStorage       access.AuditStorage
	InventoryClient    access.InventoryClient
	OrderClient        access.OrderClient
	PSPClient          access.PSPClient
}

type handler struct {
	cartStorage        access.CartStorage
	idempotencyStorage access.IdempotencyStorage
	couponStorage      access.CouponStorage
	captureStorage     access.CaptureStorage
	outboxStorage      access.OutboxStorage
	auditStorage       access.AuditStorage
	inventoryClient    access.InventoryClient
	orderClient        access.OrderClient
	pspClient          access.PSPClient
	now                func() time.Time
}

// NewHandler builds the checkout domain handler from its dependencies.
func NewHandler(cfg HandlerConfig) *handler {
	return &handler{
		cartStorage:        cfg.CartStorage,
		idempotencyStorage: cfg.IdempotencyStorage,
		couponStorage:      cfg.CouponStorage,
		captureStorage:     cfg.CaptureStorage,
		outboxStorage:      cfg.OutboxStorage,
		auditStorage:       cfg.AuditStorage,
		inventoryClient:    cfg.InventoryClient,
		orderClient:        cfg.OrderClient,
		pspClient:          cfg.PSPClient,
		now:                func() time.Time { return time.Now().UTC() },
	}
}

func (h *handler) audit(ctx context.Context, eventType, target string) {
	ev := access.AuditEvent{
		AuditID:   uuid.NewString(),
		EventType: eventType,
		Actor:     target,
		Action:    eventType,
		Target:    target,
		Timestamp: h.now(),
	}
	if err := h.auditStorage.Append(ctx, ev); err != nil {
		slog.WarnContext(ctx, "failed to append audit event",
			slog.String("event_type", eventType), slog.String("error", err.Error()))
	}
}
