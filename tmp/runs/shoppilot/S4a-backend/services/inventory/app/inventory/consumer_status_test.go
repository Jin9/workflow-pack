package inventory

import (
	"context"
	"encoding/json"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/common/kafka"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func statusMsg(t *testing.T, payload StatusChangedMessage) kafka.Message[json.RawMessage] {
	t.Helper()
	raw, err := json.Marshal(payload)
	require.NoError(t, err)
	return kafka.Message[json.RawMessage]{EventID: "evt-1", Payload: raw}
}

func TestOnStatusChanged(t *testing.T) {
	const (
		orderID       = "33333333-3333-3333-3333-333333333333"
		reservationID = "44444444-4444-4444-4444-444444444444"
	)

	reservedFixture := func() access.Reservation {
		return access.Reservation{
			ReservationID: reservationID,
			Status:        access.ReservationStatusReserved,
			Items:         []access.ReservationItem{{SKU: "SKU-A", Qty: 2}},
		}
	}

	t.Run("cancellation releases the reservation", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(reservedFixture(), nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{SKU: "SKU-A", Available: 8}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-A", 10).Return(nil)
		d.reservation.EXPECT().Release(mock.Anything, reservationID).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.released")).Return(nil)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID, Status: "cancelled",
		}))

		r.NoError(err)
	})

	t.Run("non-cancellation status is an acknowledged no-op", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID, Status: "paid",
		}))

		r.NoError(err)
	})

	t.Run("cancellation for an unknown reservation is idempotently acknowledged", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, access.ErrReservationNotFound)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID, Status: "cancelled",
		}))

		r.NoError(err)
	})

	t.Run("cancellation for an already-released reservation is idempotently acknowledged", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		released := reservedFixture()
		released.Status = access.ReservationStatusReleased
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(released, nil)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID, Status: "cancelled",
		}))

		r.NoError(err)
	})

	t.Run("invalid JSON payload is an error", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnStatusChanged(context.Background(), kafka.Message[json.RawMessage]{
			EventID: "evt-1", Payload: []byte("{ invalid json"),
		})

		r.Error(err)
	})

	t.Run("missing reservationId fails binding validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, Status: "cancelled",
		}))

		r.Error(err)
	})

	t.Run("missing orderId fails binding validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			ReservationID: reservationID, Status: "cancelled",
		}))

		r.Error(err)
	})

	t.Run("missing status fails binding validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID,
		}))

		r.Error(err)
	})

	t.Run("a non-not-found release error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, errors.New("firestore down"))

		err := h.OnStatusChanged(context.Background(), statusMsg(t, StatusChangedMessage{
			OrderID: orderID, ReservationID: reservationID, Status: "cancelled",
		}))

		r.Error(err)
	})
}
