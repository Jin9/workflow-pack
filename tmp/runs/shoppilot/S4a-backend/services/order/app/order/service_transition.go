package order

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/google/uuid"
)

const roleAdmin = "admin"

var (
	// ErrIllegalBackward is returned for any transition that is not allowed by the
	// forward-only state machine (backward, self, terminal-source, or unknown state).
	ErrIllegalBackward = errors.New("illegal state transition")
	// ErrMissingTrackingOnShipped is returned when transitioning to "shipped"
	// without a tracking number.
	ErrMissingTrackingOnShipped = errors.New("tracking number required to mark order shipped")
	// ErrNotAdmin is returned when a non-admin attempts a transition. The handler
	// enforces the role gate before reaching the service, but this sentinel keeps
	// the policy explicit and testable at the domain layer.
	ErrNotAdmin = errors.New("transition requires admin role")
)

// orderState is the type for the order state-machine vertices.
type orderState string

const (
	stateAwaitingPayment orderState = access.OrderStateAwaitingPayment
	statePaid            orderState = access.OrderStatePaid
	statePacking         orderState = access.OrderStatePacking
	stateShipped         orderState = access.OrderStateShipped
	stateDelivered       orderState = access.OrderStateDelivered
	statePaymentFailed   orderState = access.OrderStatePaymentFailed
	statePaymentTimeout  orderState = access.OrderStatePaymentTimeout
	stateCancelled       orderState = access.OrderStateCancelled
)

// allowedTransitions is the forward-only state machine. Each key lists the states
// reachable in one step. Terminal states (delivered, payment_failed,
// payment_timeout, cancelled) have no outgoing edges. awaiting_payment may be
// cancelled (e.g. checkout abandoned) and paid; the happy path then runs
// paid -> packing -> shipped -> delivered. cancelled is reachable while the order
// has not yet shipped.
var allowedTransitions = map[orderState]map[orderState]bool{
	stateAwaitingPayment: {
		statePaid:           true,
		statePaymentFailed:  true,
		statePaymentTimeout: true,
		stateCancelled:      true,
	},
	statePaid: {
		statePacking:   true,
		stateCancelled: true,
	},
	statePacking: {
		stateShipped:   true,
		stateCancelled: true,
	},
	stateShipped: {
		stateDelivered: true,
	},
	stateDelivered:      {},
	statePaymentFailed:  {},
	statePaymentTimeout: {},
	stateCancelled:      {},
}

// canTransition is a pure validator for the forward-only state machine. It returns
// true only when an edge from -> to exists in allowedTransitions. Unknown states,
// self-loops, backward moves, and edges out of a terminal state all return false.
func canTransition(from, to orderState) bool {
	next, ok := allowedTransitions[from]
	if !ok {
		return false
	}
	return next[to]
}

// transition advances an order's state under the forward-only machine. It rejects
// illegal/backward moves (ErrIllegalBackward) and a "shipped" target without a
// tracking number (ErrMissingTrackingOnShipped). On success it persists the new
// state, emits the order.status.changed audit event (ADR-006) and appends the
// matching outbox row for downstream publication (ADR-008).
func (h *handler) transition(ctx context.Context, orderNo, targetState, trackingNo string) (access.Order, error) {
	order, err := h.orderStorage.GetByOrderNo(ctx, orderNo)
	if err != nil {
		if errors.Is(err, access.ErrOrderNotFound) {
			return access.Order{}, ErrNotFound
		}
		return access.Order{}, serror.Wrap(err).With(slog.String("order_no", orderNo))
	}

	from := orderState(order.State)
	to := orderState(targetState)

	if !canTransition(from, to) {
		return access.Order{}, fmt.Errorf("%w: %s -> %s", ErrIllegalBackward, order.State, targetState)
	}

	if to == stateShipped && trackingNo == "" {
		return access.Order{}, ErrMissingTrackingOnShipped
	}

	if err := h.orderStorage.UpdateState(ctx, orderNo, targetState, trackingNo); err != nil {
		return access.Order{}, fmt.Errorf("failed to persist order state: %w", err)
	}

	if err := h.appendStatusChangedOutbox(ctx, order.OrderNo, order.State, targetState); err != nil {
		return access.Order{}, err
	}

	h.audit(ctx, eventOrderStatusChanged, roleAdmin, order.OrderNo)

	order.State = targetState
	if trackingNo != "" {
		order.TrackingNo = trackingNo
	}
	return order, nil
}

// appendStatusChangedOutbox records the order.status.changed event in the
// transactional outbox (ADR-008) so it is published exactly-once by the relay.
func (h *handler) appendStatusChangedOutbox(ctx context.Context, orderNo, from, to string) error {
	payload := fmt.Sprintf(`{"orderNo":%q,"from":%q,"to":%q}`, orderNo, from, to)
	ev := access.OutboxEvent{
		EventID:     uuid.NewString(),
		EventName:   eventOrderStatusChanged,
		AggregateID: orderNo,
		Payload:     payload,
		CreatedAt:   h.now(),
	}
	if err := h.outboxStorage.Append(ctx, ev); err != nil {
		return fmt.Errorf("failed to append status-changed outbox event: %w", err)
	}
	return nil
}
