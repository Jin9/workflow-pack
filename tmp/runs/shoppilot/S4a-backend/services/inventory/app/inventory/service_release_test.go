package inventory

import (
	"context"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func TestRelease(t *testing.T) {
	const reservationID = "22222222-2222-2222-2222-222222222222"
	reservedFixture := func() access.Reservation {
		return access.Reservation{
			ReservationID: reservationID,
			Status:        access.ReservationStatusReserved,
			Items:         []access.ReservationItem{{SKU: "SKU-A", Qty: 2}, {SKU: "SKU-B", Qty: 1}},
		}
	}

	t.Run("releasing a reserved reservation restores each sku, marks released, audits", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(reservedFixture(), nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{SKU: "SKU-A", Available: 8}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-A", 10).Return(nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-B").Return(access.Stock{SKU: "SKU-B", Available: 4}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-B", 5).Return(nil)
		d.reservation.EXPECT().Release(mock.Anything, reservationID).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.released")).Return(nil)

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.NoError(err)
	})

	t.Run("already-released reservation is an idempotent no-op (no stock mutation, no audit)", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		released := reservedFixture()
		released.Status = access.ReservationStatusReleased
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(released, nil)

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.NoError(err)
	})

	t.Run("unknown reservation surfaces ErrReservationNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, access.ErrReservationNotFound)

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.ErrorIs(err, access.ErrReservationNotFound)
	})

	t.Run("unexpected lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, errors.New("firestore down"))

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.Error(err)
		r.NotErrorIs(err, access.ErrReservationNotFound)
	})

	t.Run("stock read failure during restore is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(reservedFixture(), nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{}, errors.New("db down"))

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.Error(err)
	})

	t.Run("stock write failure during restore is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(reservedFixture(), nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{SKU: "SKU-A", Available: 8}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-A", 10).Return(errors.New("write failed"))

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.Error(err)
	})

	t.Run("reservation release write failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		single := access.Reservation{
			ReservationID: reservationID,
			Status:        access.ReservationStatusReserved,
			Items:         []access.ReservationItem{{SKU: "SKU-A", Qty: 2}},
		}
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(single, nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{SKU: "SKU-A", Available: 8}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-A", 10).Return(nil)
		d.reservation.EXPECT().Release(mock.Anything, reservationID).Return(errors.New("write failed"))

		err := h.release(context.Background(), reservationID, "order.cancelled")

		r.Error(err)
	})
}
