package inventory

import (
	"context"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func TestAdjust(t *testing.T) {
	const sku = "SKU-A"

	t.Run("setting available at or above reserved succeeds and audits adjusted", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 10).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.adjusted")).Return(nil)

		err := h.adjust(context.Background(), sku, 10, "restock")

		r.NoError(err)
	})

	t.Run("new available exactly equal to reserved is allowed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 3).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("stock.adjusted")).Return(nil)

		err := h.adjust(context.Background(), sku, 3, "shrinkage")

		r.NoError(err)
	})

	t.Run("new available below reserved surfaces ErrBelowReserved", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)

		err := h.adjust(context.Background(), sku, 2, "shrinkage")

		r.ErrorIs(err, access.ErrBelowReserved)
	})

	t.Run("unknown sku surfaces ErrSKUNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{}, access.ErrSKUNotFound)

		err := h.adjust(context.Background(), sku, 10, "restock")

		r.ErrorIs(err, access.ErrSKUNotFound)
	})

	t.Run("unexpected lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{}, errors.New("db down"))

		err := h.adjust(context.Background(), sku, 10, "restock")

		r.Error(err)
		r.NotErrorIs(err, access.ErrSKUNotFound)
	})

	t.Run("sku deleted between read and write surfaces ErrSKUNotFound", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 10).Return(access.ErrSKUNotFound)

		err := h.adjust(context.Background(), sku, 10, "restock")

		r.ErrorIs(err, access.ErrSKUNotFound)
	})

	t.Run("unexpected write error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 10).Return(errors.New("write failed"))

		err := h.adjust(context.Background(), sku, 10, "restock")

		r.Error(err)
		r.NotErrorIs(err, access.ErrSKUNotFound)
	})
}
