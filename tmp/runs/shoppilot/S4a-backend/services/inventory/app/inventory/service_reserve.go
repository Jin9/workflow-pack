package inventory

import (
	"context"
	"errors"
	"log/slog"
	"time"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/google/uuid"
)

// timeLayout is the wire format for reservation deadlines in API responses.
const timeLayout = time.RFC3339

// reserve idempotently holds stock for an order. A confirmId already on record
// returns its existing reservation WITHOUT decrementing again (ADR-004). On a
// fresh confirmId each item is atomically decremented (ADR-002); any failure
// surfaces ErrInsufficientStock or ErrSKUNotFound. Success persists a 30m-TTL
// reservation and emits stock.reserved (ADR-006).
func (h *handler) reserve(ctx context.Context, confirmID string, items []ReserveItem) (access.Reservation, error) {
	existing, err := h.reservationStorage.GetByConfirmID(ctx, confirmID)
	if err == nil {
		return existing, nil
	}
	if !errors.Is(err, access.ErrReservationNotFound) {
		return access.Reservation{}, serror.Wrap(err).With(slog.String("confirm_id", confirmID))
	}

	reservedItems := make([]access.ReservationItem, 0, len(items))
	for _, item := range items {
		if _, err := h.stockStorage.ConditionalDecrement(ctx, item.SKU, item.Qty); err != nil {
			if errors.Is(err, access.ErrInsufficientStock) || errors.Is(err, access.ErrSKUNotFound) {
				return access.Reservation{}, err
			}
			return access.Reservation{}, serror.Wrap(err).With(
				slog.String("confirm_id", confirmID),
				slog.String("sku", item.SKU),
			)
		}
		reservedItems = append(reservedItems, access.ReservationItem{SKU: item.SKU, Qty: item.Qty})
	}

	now := h.now()
	reservation := access.Reservation{
		ReservationID: uuid.NewString(),
		ConfirmID:     confirmID,
		Items:         reservedItems,
		Status:        access.ReservationStatusReserved,
		ExpiresAt:     now.Add(reservationTTL),
	}

	created, err := h.reservationStorage.Create(ctx, reservation)
	if err != nil {
		return access.Reservation{}, serror.Wrap(err).With(slog.String("confirm_id", confirmID))
	}

	h.audit(ctx, "stock.reserved", created.ReservationID)
	return created, nil
}
