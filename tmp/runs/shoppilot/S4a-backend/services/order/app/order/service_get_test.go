package order

import (
	"context"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/order/app/order/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func ownedOrder() access.Order {
	return access.Order{
		OrderNo: "order-1",
		State:   access.OrderStatePaid,
		Snapshot: access.Snapshot{
			CustomerID: "member-123",
			TotalMinor: 1000,
		},
	}
}

func TestGet(t *testing.T) {
	t.Run("owner reads their own order", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(ownedOrder(), nil)

		out, err := h.get(context.Background(), "order-1", "member-123")
		r.NoError(err)
		r.Equal("order-1", out.OrderNo)
	})

	t.Run("non-owner is rejected with ErrNotOwner", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(ownedOrder(), nil)

		_, err := h.get(context.Background(), "order-1", "member-999")
		r.ErrorIs(err, ErrNotOwner)
	})

	t.Run("unknown order maps to ErrNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "missing").Return(access.Order{}, access.ErrOrderNotFound)

		_, err := h.get(context.Background(), "missing", "member-123")
		r.ErrorIs(err, ErrNotFound)
	})

	t.Run("unexpected storage error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.order.EXPECT().GetByOrderNo(mock.Anything, "order-1").Return(access.Order{}, errors.New("firestore down"))

		_, err := h.get(context.Background(), "order-1", "member-123")
		r.Error(err)
		r.NotErrorIs(err, ErrNotFound)
		r.NotErrorIs(err, ErrNotOwner)
	})
}
