package order

import (
	"context"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

// TestCanTransition exhaustively exercises the pure forward-only state-machine
// validator: every allowed edge accepted, and a representative set of rejected
// edges (backward, self, skip-ahead, out-of-terminal, unknown state).
func TestCanTransition(t *testing.T) {
	allowed := []struct{ from, to orderState }{
		{stateAwaitingPayment, statePaid},
		{stateAwaitingPayment, statePaymentFailed},
		{stateAwaitingPayment, statePaymentTimeout},
		{stateAwaitingPayment, stateCancelled},
		{statePaid, statePacking},
		{statePaid, stateCancelled},
		{statePacking, stateShipped},
		{statePacking, stateCancelled},
		{stateShipped, stateDelivered},
	}
	for _, tc := range allowed {
		t.Run("allow "+string(tc.from)+"->"+string(tc.to), func(t *testing.T) {
			require.True(t, canTransition(tc.from, tc.to))
		})
	}

	rejected := []struct{ from, to orderState }{
		// backward
		{statePaid, stateAwaitingPayment},
		{statePacking, statePaid},
		{stateShipped, statePacking},
		{stateDelivered, stateShipped},
		// skip-ahead
		{stateAwaitingPayment, statePacking},
		{stateAwaitingPayment, stateShipped},
		{statePaid, stateShipped},
		{statePaid, stateDelivered},
		{statePacking, stateDelivered},
		// self-loops
		{stateAwaitingPayment, stateAwaitingPayment},
		{statePaid, statePaid},
		{stateShipped, stateShipped},
		// out of terminal states
		{stateDelivered, stateCancelled},
		{statePaymentFailed, statePaid},
		{statePaymentTimeout, statePaid},
		{stateCancelled, statePaid},
		{stateShipped, stateCancelled},
		// unknown / invalid states
		{orderState("bogus"), statePaid},
		{statePaid, orderState("bogus")},
		{orderState(""), statePaid},
	}
	for _, tc := range rejected {
		t.Run("reject "+string(tc.from)+"->"+string(tc.to), func(t *testing.T) {
			require.False(t, canTransition(tc.from, tc.to))
		})
	}
}

func paidOrder() access.Order {
	return access.Order{OrderNo: "order-1", State: access.OrderStatePaid}
}

func TestTransition(t *testing.T) {
	t.Run("legal transition persists, appends outbox, audits status changed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paidOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, "order-1", access.OrderStatePacking, "").Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.MatchedBy(func(e access.OutboxEvent) bool {
			return e.EventName == eventOrderStatusChanged && e.AggregateID == "order-1" && e.EventID != ""
		})).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventOrderStatusChanged)).Return(nil)

		out, err := h.transition(context.Background(), "order-1", access.OrderStatePacking, "")
		r.NoError(err)
		r.Equal(access.OrderStatePacking, out.State)
	})

	t.Run("shipped with tracking number persists tracking", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		packing := access.Order{OrderNo: "order-1", State: access.OrderStatePacking}
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(packing, nil)
		d.order.EXPECT().UpdateState(mock.Anything, "order-1", access.OrderStateShipped, "TRACK-1").Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventOrderStatusChanged)).Return(nil)

		out, err := h.transition(context.Background(), "order-1", access.OrderStateShipped, "TRACK-1")
		r.NoError(err)
		r.Equal(access.OrderStateShipped, out.State)
		r.Equal("TRACK-1", out.TrackingNo)
	})

	t.Run("shipped without tracking number is rejected", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		packing := access.Order{OrderNo: "order-1", State: access.OrderStatePacking}
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(packing, nil)

		_, err := h.transition(context.Background(), "order-1", access.OrderStateShipped, "")
		r.ErrorIs(err, ErrMissingTrackingOnShipped)
	})

	t.Run("illegal backward transition is rejected", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paidOrder(), nil)

		_, err := h.transition(context.Background(), "order-1", access.OrderStateAwaitingPayment, "")
		r.ErrorIs(err, ErrIllegalBackward)
	})

	t.Run("unknown order maps to ErrNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "missing").Return(access.Order{}, access.ErrOrderNotFound)

		_, err := h.transition(context.Background(), "missing", access.OrderStatePacking, "")
		r.ErrorIs(err, ErrNotFound)
	})

	t.Run("unexpected lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(access.Order{}, errors.New("firestore down"))

		_, err := h.transition(context.Background(), "order-1", access.OrderStatePacking, "")
		r.Error(err)
		r.NotErrorIs(err, ErrNotFound)
	})

	t.Run("update persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paidOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, "order-1", access.OrderStatePacking, "").Return(errors.New("write failed"))

		_, err := h.transition(context.Background(), "order-1", access.OrderStatePacking, "")
		r.Error(err)
	})

	t.Run("outbox append failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(paidOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, "order-1", access.OrderStatePacking, "").Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(errors.New("outbox down"))

		_, err := h.transition(context.Background(), "order-1", access.OrderStatePacking, "")
		r.Error(err)
	})
}
