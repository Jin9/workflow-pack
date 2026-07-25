package inventory

import (
	"context"
	"errors"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"
)

// release is the SAGA compensation for a reservation (ADR-004). It returns each
// held SKU's quantity to available, marks the reservation released, and emits
// stock.released (ADR-006). It is idempotent: an already-released reservation
// short-circuits without re-incrementing stock, so a retried compensation (or a
// TTL sweep racing the order cancellation) can never double-credit inventory.
func (h *handler) release(ctx context.Context, reservationID, reason string) error {
	reservation, err := h.reservationStorage.GetByID(ctx, reservationID)
	if err != nil {
		if errors.Is(err, access.ErrReservationNotFound) {
			return err
		}
		return serror.Wrap(err).With(slog.String("reservation_id", reservationID))
	}

	if reservation.Status == access.ReservationStatusReleased {
		return nil
	}

	for _, item := range reservation.Items {
		stock, err := h.stockStorage.GetBySKU(ctx, item.SKU)
		if err != nil {
			return serror.Wrap(err).With(
				slog.String("reservation_id", reservationID),
				slog.String("sku", item.SKU),
			)
		}
		if err := h.stockStorage.SetAvailable(ctx, item.SKU, stock.Available+item.Qty); err != nil {
			return serror.Wrap(err).With(
				slog.String("reservation_id", reservationID),
				slog.String("sku", item.SKU),
			)
		}
	}

	if err := h.reservationStorage.Release(ctx, reservationID); err != nil {
		return serror.Wrap(err).With(
			slog.String("reservation_id", reservationID),
			slog.String("reason", reason),
		)
	}

	h.audit(ctx, "stock.released", reservationID)
	return nil
}
