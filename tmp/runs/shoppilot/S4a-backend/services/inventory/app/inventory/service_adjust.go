package inventory

import (
	"context"
	"errors"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"
)

// adjust sets a SKU's absolute available count. It enforces the core invariant
// available >= reserved: an adjustment that would orphan already-reserved stock
// is rejected with ErrBelowReserved. An unknown SKU surfaces ErrSKUNotFound.
// Success emits stock.adjusted (ADR-006).
func (h *handler) adjust(ctx context.Context, sku string, newAvailable int, reason string) error {
	stock, err := h.stockStorage.GetBySKU(ctx, sku)
	if err != nil {
		if errors.Is(err, access.ErrSKUNotFound) {
			return err
		}
		return serror.Wrap(err).With(slog.String("sku", sku))
	}

	if newAvailable < stock.Reserved {
		return access.ErrBelowReserved
	}

	if err := h.stockStorage.SetAvailable(ctx, sku, newAvailable); err != nil {
		if errors.Is(err, access.ErrSKUNotFound) {
			return err
		}
		return serror.Wrap(err).With(
			slog.String("sku", sku),
			slog.String("reason", reason),
		)
	}

	h.audit(ctx, "stock.adjusted", sku)
	return nil
}
