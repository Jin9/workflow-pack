package order

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/google/uuid"
)

// create confirms an order idempotently. If an order already exists for the
// confirmId it is returned unchanged (no new order, no duplicate audit); a fresh
// order freezes the immutable snapshot, starts in awaiting_payment, and emits
// order.confirmed (ADR-003, ADR-006).
func (h *handler) create(ctx context.Context, req CreateOrderRequest) (access.Order, error) {
	existing, err := h.orderStorage.GetByConfirmID(ctx, req.ConfirmID)
	if err == nil {
		return existing, nil
	}
	if !errors.Is(err, access.ErrOrderNotFound) {
		return access.Order{}, serror.Wrap(err).With(slog.String("confirm_id", req.ConfirmID))
	}

	order := access.Order{
		OrderNo:   uuid.NewString(),
		ConfirmID: req.ConfirmID,
		Snapshot:  toSnapshot(req.Snapshot),
		State:     access.OrderStateAwaitingPayment,
	}

	created, err := h.orderStorage.Create(ctx, order)
	if err != nil {
		return access.Order{}, fmt.Errorf("failed to create order: %w", err)
	}

	h.audit(ctx, eventOrderConfirmed, created.Snapshot.CustomerID, created.OrderNo)
	return created, nil
}

func toSnapshot(req SnapshotRequest) access.Snapshot {
	items := make([]access.OrderItem, 0, len(req.Items))
	for _, it := range req.Items {
		items = append(items, access.OrderItem{
			SKU:        it.SKU,
			Name:       it.Name,
			Quantity:   it.Quantity,
			PriceMinor: it.PriceMinor,
		})
	}
	return access.Snapshot{
		CustomerID: req.CustomerID,
		Items:      items,
		TotalMinor: req.TotalMinor,
		Address:    req.Address,
	}
}

func toCreateResponse(order access.Order) *CreateOrderResponse {
	return &CreateOrderResponse{
		OrderNo:   order.OrderNo,
		State:     order.State,
		ConfirmID: order.ConfirmID,
		Snapshot:  toSnapshotPayload(order.Snapshot),
	}
}

func toSnapshotPayload(snap access.Snapshot) SnapshotPayload {
	items := make([]OrderItemPayload, 0, len(snap.Items))
	for _, it := range snap.Items {
		items = append(items, OrderItemPayload{
			SKU:        it.SKU,
			Name:       it.Name,
			Quantity:   it.Quantity,
			PriceMinor: it.PriceMinor,
		})
	}
	return SnapshotPayload{
		CustomerID: snap.CustomerID,
		Items:      items,
		TotalMinor: snap.TotalMinor,
		Address:    snap.Address,
	}
}
