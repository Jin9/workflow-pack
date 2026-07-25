package order

import (
	"context"
	"encoding/json"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/common/kafka"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func awaitingOrder() access.Order {
	return access.Order{OrderNo: "11111111-1111-1111-1111-111111111111", State: access.OrderStateAwaitingPayment}
}

func msgFrom(t *testing.T, payload any) kafka.Message[json.RawMessage] {
	t.Helper()
	raw, err := json.Marshal(payload)
	require.NoError(t, err)
	return kafka.Message[json.RawMessage]{EventID: "evt-1", Payload: raw}
}

func TestOnPaymentCaptured(t *testing.T) {
	const orderID = "11111111-1111-1111-1111-111111111111"

	t.Run("success advances awaiting_payment to paid and audits", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(awaitingOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, orderID, access.OrderStatePaid, "").Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventPaymentCaptured)).Return(nil)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "success", AmountMinor: 1000,
		}))
		r.NoError(err)
	})

	t.Run("failure advances awaiting_payment to payment_failed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(awaitingOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, orderID, access.OrderStatePaymentFailed, "").Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventPaymentCaptured)).Return(nil)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "failure",
		}))
		r.NoError(err)
	})

	t.Run("timeout advances awaiting_payment to payment_timeout", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(awaitingOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, orderID, access.OrderStatePaymentTimeout, "").Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventPaymentCaptured)).Return(nil)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "timeout",
		}))
		r.NoError(err)
	})

	t.Run("idempotent: order already paid is a no-op ack", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		paid := access.Order{OrderNo: orderID, State: access.OrderStatePaid}
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(paid, nil)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "success",
		}))
		r.NoError(err)
	})

	t.Run("invalid JSON payload is an error", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)
		msg := kafka.Message[json.RawMessage]{EventID: "evt-1", Payload: json.RawMessage("{ invalid json")}

		err := h.OnPaymentCaptured(context.Background(), msg)
		r.Error(err)
	})

	t.Run("missing orderId fails validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{Outcome: "success"}))
		r.Error(err)
	})

	t.Run("orderId not a uuid fails validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: "not-a-uuid", Outcome: "success",
		}))
		r.Error(err)
	})

	t.Run("missing outcome fails validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{OrderID: orderID}))
		r.Error(err)
	})

	t.Run("unknown outcome fails validation", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandlerForTest(t)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "bogus",
		}))
		r.Error(err)
	})

	t.Run("unknown order is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(access.Order{}, access.ErrOrderNotFound)

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "success",
		}))
		r.Error(err)
	})

	t.Run("unexpected lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(access.Order{}, errors.New("firestore down"))

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "success",
		}))
		r.Error(err)
	})

	t.Run("update persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, orderID).Return(awaitingOrder(), nil)
		d.order.EXPECT().UpdateState(mock.Anything, orderID, access.OrderStatePaid, "").Return(errors.New("write failed"))

		err := h.OnPaymentCaptured(context.Background(), msgFrom(t, PaymentCapturedMessage{
			OrderID: orderID, Outcome: "success",
		}))
		r.Error(err)
	})

	t.Run("stateForOutcome rejects unknown outcome", func(t *testing.T) {
		r := require.New(t)
		_, err := stateForOutcome("nope")
		r.Error(err)
	})
}
