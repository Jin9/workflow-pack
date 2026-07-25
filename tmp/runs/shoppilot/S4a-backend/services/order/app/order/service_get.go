package order

import (
	"context"
	"errors"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/order/app/order/access"
)

var (
	// ErrNotFound is returned when the order number resolves to no order.
	ErrNotFound = errors.New("order not found")
	// ErrNotOwner is returned when the requester is not the order's customer.
	// Own-data-only: a member may only read their own orders.
	ErrNotOwner = errors.New("requester is not the order owner")
)

// get loads an order and enforces own-data-only access: the requesting member id
// must equal the order's customer id, otherwise ErrNotOwner. Unknown orders map
// to ErrNotFound (never leak existence to a non-owner via a different status here —
// the lookup happens first, then ownership is checked).
func (h *handler) get(ctx context.Context, orderNo, memberID string) (access.Order, error) {
	order, err := h.orderStorage.GetByOrderNo(ctx, orderNo)
	if err != nil {
		if errors.Is(err, access.ErrOrderNotFound) {
			return access.Order{}, ErrNotFound
		}
		return access.Order{}, serror.Wrap(err).With(slog.String("order_no", orderNo))
	}

	if order.Snapshot.CustomerID != memberID {
		return access.Order{}, ErrNotOwner
	}

	return order, nil
}
