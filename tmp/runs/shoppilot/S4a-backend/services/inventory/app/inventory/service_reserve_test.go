package inventory

import (
	"context"
	"errors"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"
	access_mocks "gitlab.com/example-org/platform/backend/inventory/app/inventory/access/mocks"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

var fixedNow = time.Date(2026, 6, 7, 12, 0, 0, 0, time.UTC)

type deps struct {
	stock       *access_mocks.StockStorageMock
	reservation *access_mocks.ReservationStorageMock
	audit       *access_mocks.AuditStorageMock
}

func newHandlerForTest(t *testing.T) (*handler, deps) {
	t.Helper()
	d := deps{
		stock:       access_mocks.NewStockStorageMock(t),
		reservation: access_mocks.NewReservationStorageMock(t),
		audit:       access_mocks.NewAuditStorageMock(t),
	}
	h := NewHandler(HandlerConfig{
		StockStorage:       d.stock,
		ReservationStorage: d.reservation,
		AuditStorage:       d.audit,
	})
	h.now = func() time.Time { return fixedNow }
	return h, d
}

func auditOf(eventType string) interface{} {
	return mock.MatchedBy(func(e access.AuditEvent) bool { return e.EventType == eventType })
}

func TestReserve(t *testing.T) {
	const confirmID = "11111111-1111-1111-1111-111111111111"
	items := []ReserveItem{{SKU: "SKU-A", Qty: 2}, {SKU: "SKU-B", Qty: 1}}

	t.Run("fresh confirmId decrements each item, persists a 30m reservation, audits reserved", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(8, nil)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-B", 1).Return(4, nil)
		d.reservation.EXPECT().Create(mock.Anything, mock.MatchedBy(func(res access.Reservation) bool {
			return res.ConfirmID == confirmID &&
				res.Status == access.ReservationStatusReserved &&
				res.ExpiresAt.Equal(fixedNow.Add(30*time.Minute)) &&
				len(res.Items) == 2
		})).Return(access.Reservation{ReservationID: "res-1", ConfirmID: confirmID, ExpiresAt: fixedNow.Add(30 * time.Minute)}, nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.reserved")).Return(nil)

		res, err := h.reserve(context.Background(), confirmID, items)

		r.NoError(err)
		r.Equal("res-1", res.ReservationID)
		r.Equal(fixedNow.Add(30*time.Minute), res.ExpiresAt)
	})

	t.Run("repeated confirmId returns the existing reservation without re-decrementing", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		existing := access.Reservation{ReservationID: "res-existing", ConfirmID: confirmID}
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(existing, nil)

		res, err := h.reserve(context.Background(), confirmID, items)

		r.NoError(err)
		r.Equal("res-existing", res.ReservationID)
	})

	t.Run("insufficient stock surfaces ErrInsufficientStock", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(1, access.ErrInsufficientStock)

		_, err := h.reserve(context.Background(), confirmID, items)

		r.ErrorIs(err, access.ErrInsufficientStock)
	})

	t.Run("unknown sku surfaces ErrSKUNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(0, access.ErrSKUNotFound)

		_, err := h.reserve(context.Background(), confirmID, items)

		r.ErrorIs(err, access.ErrSKUNotFound)
	})

	t.Run("unexpected idempotency lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, errors.New("firestore down"))

		_, err := h.reserve(context.Background(), confirmID, items)

		r.Error(err)
		r.NotErrorIs(err, access.ErrReservationNotFound)
	})

	t.Run("unexpected decrement error is propagated, not classified as a stock error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(0, errors.New("db down"))

		_, err := h.reserve(context.Background(), confirmID, items)

		r.Error(err)
		r.NotErrorIs(err, access.ErrInsufficientStock)
		r.NotErrorIs(err, access.ErrSKUNotFound)
	})

	t.Run("audit append failure is logged but does not fail the reservation", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(8, nil)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-B", 1).Return(4, nil)
		d.reservation.EXPECT().Create(mock.Anything, mock.Anything).Return(access.Reservation{ReservationID: "res-1"}, nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.reserved")).Return(errors.New("audit store down"))

		res, err := h.reserve(context.Background(), confirmID, items)

		r.NoError(err)
		r.Equal("res-1", res.ReservationID)
	})

	t.Run("reservation persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(8, nil)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-B", 1).Return(4, nil)
		d.reservation.EXPECT().Create(mock.Anything, mock.Anything).Return(access.Reservation{}, errors.New("write failed"))

		_, err := h.reserve(context.Background(), confirmID, items)

		r.Error(err)
	})
}
