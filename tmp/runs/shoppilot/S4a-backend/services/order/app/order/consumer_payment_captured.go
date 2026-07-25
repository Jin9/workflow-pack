package order

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/kafka"
	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/order/app/order/access"
)

// Payment outcome values carried by the order.payment.captured event.
const (
	paymentOutcomeSuccess = "success"
	paymentOutcomeFailure = "failure"
	paymentOutcomeTimeout = "timeout"
)

// PaymentCapturedMessage is the payload contract for the order.payment.captured
// Kafka event, emitted by checkout once a payment attempt resolves. The set of
// valid outcomes is enforced by stateForOutcome (single source of truth) rather
// than a binding tag, so an unrecognised outcome surfaces a descriptive error.
type PaymentCapturedMessage struct {
	OrderID     string `json:"orderId" binding:"required,uuid"`
	Outcome     string `json:"outcome" binding:"required"`
	AmountMinor int    `json:"amountMinor"`
}

// OnPaymentCaptured consumes order.payment.captured and advances the order out of
// awaiting_payment: success -> paid, failure -> payment_failed, timeout ->
// payment_timeout. It is idempotent — an order already past awaiting_payment (a
// redelivered event) is acknowledged without a duplicate state change. Signature
// must match kafka.KafkaHandler.
func (h *handler) OnPaymentCaptured(ctx context.Context, msg kafka.Message[json.RawMessage]) error {
	var payload PaymentCapturedMessage
	if err := kafka.BindMessage(msg.Payload, &payload); err != nil {
		return serror.Wrap(err).With(slog.String("event_id", msg.EventID))
	}

	target, err := stateForOutcome(payload.Outcome)
	if err != nil {
		return serror.Wrap(err).With(
			slog.String("event_id", msg.EventID),
			slog.String("order_id", payload.OrderID),
			slog.String("outcome", payload.Outcome),
		)
	}

	order, err := h.orderStorage.GetByOrderNo(ctx, payload.OrderID)
	if err != nil {
		// Both an unknown order and an infra error are returned so the message is
		// retried (an order should exist before payment.captured arrives).
		return serror.Wrap(err).With(
			slog.String("event_id", msg.EventID),
			slog.String("order_id", payload.OrderID),
		)
	}

	// Idempotency: only an order still awaiting payment is advanced. A redelivery
	// (order already paid/failed/timed-out or further along) is a no-op ack.
	if order.State != access.OrderStateAwaitingPayment {
		slog.InfoContext(ctx, "payment.captured ignored; order not awaiting payment",
			slog.String("event_id", msg.EventID),
			slog.String("order_no", order.OrderNo),
			slog.String("state", order.State),
		)
		return nil
	}

	if err := h.orderStorage.UpdateState(ctx, order.OrderNo, target, ""); err != nil {
		return serror.Wrap(err).With(
			slog.String("event_id", msg.EventID),
			slog.String("order_no", order.OrderNo),
		)
	}

	h.audit(ctx, eventPaymentCaptured, order.OrderNo, target)
	return nil
}

// stateForOutcome maps a payment outcome to the target order state.
func stateForOutcome(outcome string) (string, error) {
	switch outcome {
	case paymentOutcomeSuccess:
		return access.OrderStatePaid, nil
	case paymentOutcomeFailure:
		return access.OrderStatePaymentFailed, nil
	case paymentOutcomeTimeout:
		return access.OrderStatePaymentTimeout, nil
	default:
		return "", fmt.Errorf("unknown payment outcome: %s", outcome)
	}
}
