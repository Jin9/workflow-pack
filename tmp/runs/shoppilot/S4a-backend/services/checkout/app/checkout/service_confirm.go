package checkout

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/google/uuid"
)

var (
	// ErrCouponExpired is returned when the presented coupon exists but is past its
	// expiry, or cannot be resolved (an unknown coupon is treated as not applicable).
	ErrCouponExpired = errors.New("coupon expired")
	// ErrOutOfStock re-exposes the inventory reservation failure at the domain layer.
	ErrOutOfStock = access.ErrOutOfStock
)

const eventOrderPurchaseCreated = "order.purchase.created"

type confirmResult struct {
	OrderID    string
	TotalMinor int
}

// confirm runs the checkout orchestration (ADR-007 sync, ADR-008 outbox, ADR-006
// audit, A2 idempotency):
//  1. idempotency replay — a known key returns its stored response, untouched.
//  2. server-side total — computed from the TRUSTED cart, never the client.
//  3. coupon re-validation — expired/unknown coupon → ErrCouponExpired.
//  4. sync orchestrate — reserve stock, then create the order, inline.
//  5. outbox append — order.purchase.created.
//  6. idempotency save — make the whole flow replay-safe.
//  7. audit — order.confirmed.
func (h *handler) confirm(ctx context.Context, req ConfirmRequest) (confirmResult, error) {
	// 1) Idempotency replay.
	if record, err := h.idempotencyStorage.GetByKey(ctx, req.IdempotencyKey); err == nil {
		return confirmResult{OrderID: record.OrderID, TotalMinor: record.TotalMinor}, nil
	} else if !errors.Is(err, access.ErrIdempotencyNotFound) {
		return confirmResult{}, serror.Wrap(err).With(slog.String("idempotency_key", req.IdempotencyKey))
	}

	// Trusted cart snapshot (server-side figures only).
	cart, err := h.cartStorage.GetByID(ctx, req.CartID)
	if err != nil {
		return confirmResult{}, serror.Wrap(err).With(slog.String("cart_id", req.CartID))
	}

	// 3) Coupon re-validation → discount.
	discountMinor, err := h.resolveDiscount(ctx, req.Coupon)
	if err != nil {
		return confirmResult{}, err
	}

	// 2) Server-computed total (pure, fully tested).
	totalMinor := computeTotal(cart.SubtotalMinor, discountMinor, cart.ShippingMinor)

	confirmID := uuid.NewString()

	// 4) Sync orchestration: reserve stock, then create the order.
	if _, err := h.inventoryClient.Reserve(ctx, confirmID, cart.Items); err != nil {
		if errors.Is(err, access.ErrOutOfStock) {
			return confirmResult{}, ErrOutOfStock
		}
		return confirmResult{}, serror.Wrap(err).With(slog.String("confirm_id", confirmID))
	}

	snapshot := access.OrderSnapshot{
		CartID:        cart.CartID,
		Address:       req.Address,
		Items:         cart.Items,
		SubtotalMinor: cart.SubtotalMinor,
		DiscountMinor: discountMinor,
		ShippingMinor: cart.ShippingMinor,
		TotalMinor:    totalMinor,
	}
	orderRef, err := h.orderClient.Create(ctx, confirmID, snapshot)
	if err != nil {
		return confirmResult{}, serror.Wrap(err).With(slog.String("confirm_id", confirmID))
	}

	// 5) Transactional outbox.
	if err := h.appendPurchaseCreated(ctx, orderRef.OrderID, totalMinor); err != nil {
		return confirmResult{}, serror.Wrap(err).With(slog.String("order_id", orderRef.OrderID))
	}

	// 6) Persist idempotency record (replay-safe).
	resp := ConfirmResponse{OrderID: orderRef.OrderID, TotalMinor: totalMinor}
	encoded, err := json.Marshal(resp)
	if err != nil {
		return confirmResult{}, fmt.Errorf("failed to encode confirm response: %w", err)
	}
	rec := access.IdempotencyRecord{
		Key:        req.IdempotencyKey,
		OrderID:    orderRef.OrderID,
		TotalMinor: totalMinor,
		Response:   string(encoded),
		CreatedAt:  h.now(),
	}
	if err := h.idempotencyStorage.Save(ctx, rec); err != nil {
		return confirmResult{}, serror.Wrap(err).With(slog.String("order_id", orderRef.OrderID))
	}

	// 7) Audit.
	h.audit(ctx, "order.confirmed", orderRef.OrderID)

	return confirmResult{OrderID: orderRef.OrderID, TotalMinor: totalMinor}, nil
}

// resolveDiscount re-validates the coupon server-side. An empty code means no
// coupon. An expired coupon, or one that cannot be resolved, is rejected as
// ErrCouponExpired (an unknown code is not silently treated as a free discount).
func (h *handler) resolveDiscount(ctx context.Context, code string) (int, error) {
	if code == "" {
		return 0, nil
	}
	coupon, err := h.couponStorage.GetByCode(ctx, code)
	if err != nil {
		if errors.Is(err, access.ErrCouponNotFound) {
			return 0, ErrCouponExpired
		}
		return 0, serror.Wrap(err).With(slog.String("coupon", code))
	}
	if h.now().After(coupon.ExpiresAt) {
		return 0, ErrCouponExpired
	}
	return coupon.DiscountMinor, nil
}

func (h *handler) appendPurchaseCreated(ctx context.Context, orderID string, totalMinor int) error {
	payload, err := json.Marshal(map[string]any{"orderId": orderID, "totalMinor": totalMinor})
	if err != nil {
		return fmt.Errorf("failed to encode outbox payload: %w", err)
	}
	ev := access.OutboxEvent{
		EventID:     uuid.NewString(),
		EventType:   eventOrderPurchaseCreated,
		AggregateID: orderID,
		Payload:     string(payload),
		CreatedAt:   h.now(),
	}
	if err := h.outboxStorage.Append(ctx, ev); err != nil {
		return fmt.Errorf("failed to append purchase-created outbox event: %w", err)
	}
	return nil
}
