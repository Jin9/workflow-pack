package inventory

import (
	"context"
	"encoding/json"
	"errors"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/kafka"
	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"
)

// statusCancelled is the order status that triggers reservation release. The
// order service emits order.status.changed on every transition; inventory only
// acts on the cancellation, returning held stock via the idempotent release path.
const statusCancelled = "cancelled"

// StatusChangedMessage is the payload contract for the order.status.changed event.
type StatusChangedMessage struct {
	OrderID       string `json:"orderId" binding:"required,uuid"`
	ReservationID string `json:"reservationId" binding:"required,uuid"`
	Status        string `json:"status" binding:"required"`
}

// OnStatusChanged consumes order.status.changed. A non-cancellation status is
// acknowledged as a no-op; a cancellation releases the reservation. Release is
// idempotent and treats an unknown reservation as already-compensated, so replays
// and out-of-order delivery are safe. Signature matches kafka.KafkaHandler.
func (h *handler) OnStatusChanged(ctx context.Context, msg kafka.Message[json.RawMessage]) error {
	var payload StatusChangedMessage
	if err := kafka.BindMessage(msg.Payload, &payload); err != nil {
		return serror.Wrap(err).With(slog.String("event_id", msg.EventID))
	}

	if payload.Status != statusCancelled {
		slog.InfoContext(ctx, "order.status.changed ignored (not a cancellation)",
			slog.String("event_id", msg.EventID),
			slog.String("order_id", payload.OrderID),
			slog.String("status", payload.Status),
		)
		return nil
	}

	if err := h.release(ctx, payload.ReservationID, "order."+payload.Status); err != nil {
		if errors.Is(err, access.ErrReservationNotFound) {
			slog.InfoContext(ctx, "reservation already compensated or never created",
				slog.String("event_id", msg.EventID),
				slog.String("reservation_id", payload.ReservationID),
			)
			return nil
		}
		return serror.Wrap(err).With(
			slog.String("event_id", msg.EventID),
			slog.String("order_id", payload.OrderID),
			slog.String("reservation_id", payload.ReservationID),
		)
	}

	return nil
}
