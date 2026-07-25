package checkout

import (
	"context"
	"errors"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"
	access_mocks "gitlab.com/example-org/platform/backend/checkout/app/checkout/access/mocks"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

var fixedNow = time.Date(2026, 6, 7, 12, 0, 0, 0, time.UTC)

type deps struct {
	cart      *access_mocks.CartStorageMock
	idem      *access_mocks.IdempotencyStorageMock
	coupon    *access_mocks.CouponStorageMock
	capture   *access_mocks.CaptureStorageMock
	outbox    *access_mocks.OutboxStorageMock
	audit     *access_mocks.AuditStorageMock
	inventory *access_mocks.InventoryClientMock
	order     *access_mocks.OrderClientMock
	psp       *access_mocks.PSPClientMock
}

func newHandlerForTest(t *testing.T) (*handler, deps) {
	t.Helper()
	d := deps{
		cart:      access_mocks.NewCartStorageMock(t),
		idem:      access_mocks.NewIdempotencyStorageMock(t),
		coupon:    access_mocks.NewCouponStorageMock(t),
		capture:   access_mocks.NewCaptureStorageMock(t),
		outbox:    access_mocks.NewOutboxStorageMock(t),
		audit:     access_mocks.NewAuditStorageMock(t),
		inventory: access_mocks.NewInventoryClientMock(t),
		order:     access_mocks.NewOrderClientMock(t),
		psp:       access_mocks.NewPSPClientMock(t),
	}
	h := NewHandler(HandlerConfig{
		CartStorage:        d.cart,
		IdempotencyStorage: d.idem,
		CouponStorage:      d.coupon,
		CaptureStorage:     d.capture,
		OutboxStorage:      d.outbox,
		AuditStorage:       d.audit,
		InventoryClient:    d.inventory,
		OrderClient:        d.order,
		PSPClient:          d.psp,
	})
	h.now = func() time.Time { return fixedNow }
	return h, d
}

func auditOf(eventType string) interface{} {
	return mock.MatchedBy(func(e access.AuditEvent) bool { return e.EventType == eventType })
}

func outboxOf(eventType string) interface{} {
	return mock.MatchedBy(func(e access.OutboxEvent) bool { return e.EventType == eventType })
}

const idemKey = "11111111-1111-1111-1111-111111111111"

func sampleCart() access.Cart {
	return access.Cart{
		CartID:        "cart-1",
		Items:         []access.ReserveItem{{SKU: "SKU-1", Quantity: 2}},
		SubtotalMinor: 10000,
		ShippingMinor: 500,
	}
}

func validConfirmReq() ConfirmRequest {
	return ConfirmRequest{
		CartID:         "cart-1",
		Address:        "1 Market St",
		IdempotencyKey: idemKey,
	}
}

func TestConfirm(t *testing.T) {
	t.Run("happy path reserves, creates order, appends outbox, saves idempotency, audits", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{ReservationID: "res-1"}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.MatchedBy(func(s access.OrderSnapshot) bool {
			return s.TotalMinor == 10500 // 10000 - 0 + 500
		})).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, outboxOf("order.purchase.created")).Return(nil)
		d.idem.EXPECT().Save(mock.Anything, mock.MatchedBy(func(rec access.IdempotencyRecord) bool {
			return rec.Key == idemKey && rec.OrderID == "order-1" && rec.TotalMinor == 10500
		})).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("order.confirmed")).Return(nil)

		res, err := h.confirm(context.Background(), validConfirmReq())

		r.NoError(err)
		r.Equal("order-1", res.OrderID)
		r.Equal(10500, res.TotalMinor)
	})

	t.Run("a failing audit append does not fail the confirm (audit is best-effort)", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.Anything).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.idem.EXPECT().Save(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("order.confirmed")).Return(errors.New("audit down"))

		res, err := h.confirm(context.Background(), validConfirmReq())

		r.NoError(err)
		r.Equal("order-1", res.OrderID)
	})

	t.Run("idempotency replay returns the stored response without re-running the flow", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{
			Key: idemKey, OrderID: "order-prior", TotalMinor: 9999,
		}, nil)

		res, err := h.confirm(context.Background(), validConfirmReq())

		r.NoError(err)
		r.Equal("order-prior", res.OrderID)
		r.Equal(9999, res.TotalMinor)
		// No cart/inventory/order/outbox/idem-save/audit calls expected (mocks assert).
	})

	t.Run("unexpected idempotency lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, errors.New("firestore down"))

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.Error(err)
	})

	t.Run("valid coupon applies its discount to the server total", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := validConfirmReq()
		req.Coupon = "SAVE20"
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.coupon.EXPECT().GetByCode(mock.Anything, "SAVE20").Return(access.Coupon{
			Code: "SAVE20", DiscountMinor: 2000, ExpiresAt: fixedNow.Add(time.Hour),
		}, nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.MatchedBy(func(s access.OrderSnapshot) bool {
			return s.TotalMinor == 8500 && s.DiscountMinor == 2000 // 10000 - 2000 + 500
		})).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.idem.EXPECT().Save(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		res, err := h.confirm(context.Background(), req)

		r.NoError(err)
		r.Equal(8500, res.TotalMinor)
	})

	t.Run("expired coupon is rejected as coupon_expired", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := validConfirmReq()
		req.Coupon = "OLD"
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.coupon.EXPECT().GetByCode(mock.Anything, "OLD").Return(access.Coupon{
			Code: "OLD", DiscountMinor: 2000, ExpiresAt: fixedNow.Add(-time.Hour),
		}, nil)

		_, err := h.confirm(context.Background(), req)

		r.ErrorIs(err, ErrCouponExpired)
	})

	t.Run("unknown coupon is rejected, never silently treated as a free discount", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := validConfirmReq()
		req.Coupon = "GHOST"
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.coupon.EXPECT().GetByCode(mock.Anything, "GHOST").Return(access.Coupon{}, access.ErrCouponNotFound)

		_, err := h.confirm(context.Background(), req)

		r.ErrorIs(err, ErrCouponExpired)
	})

	t.Run("out of stock from inventory is surfaced as ErrOutOfStock, order never created", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, access.ErrOutOfStock)

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.ErrorIs(err, ErrOutOfStock)
	})

	t.Run("order creation failure is propagated, no outbox/audit", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.Anything).Return(access.OrderRef{}, errors.New("order down"))

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.Error(err)
		r.NotErrorIs(err, ErrOutOfStock)
	})

	t.Run("outbox append failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.Anything).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(errors.New("outbox down"))

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.Error(err)
	})

	t.Run("idempotency save failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.Anything).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.idem.EXPECT().Save(mock.Anything, mock.Anything).Return(errors.New("save down"))

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.Error(err)
	})

	t.Run("cart lookup failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(access.Cart{}, access.ErrCartNotFound)

		_, err := h.confirm(context.Background(), validConfirmReq())

		r.Error(err)
	})

	t.Run("unexpected coupon lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := validConfirmReq()
		req.Coupon = "X"
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.coupon.EXPECT().GetByCode(mock.Anything, "X").Return(access.Coupon{}, errors.New("coupon db down"))

		_, err := h.confirm(context.Background(), req)

		r.Error(err)
		r.NotErrorIs(err, ErrCouponExpired)
	})
}
