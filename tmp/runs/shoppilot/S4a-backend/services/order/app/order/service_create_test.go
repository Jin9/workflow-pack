package order

import (
	"context"
	"errors"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/order/app/order/access"
	access_mocks "gitlab.com/example-org/platform/backend/order/app/order/access/mocks"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

var fixedNow = time.Date(2026, 6, 7, 12, 0, 0, 0, time.UTC)

type deps struct {
	order  *access_mocks.OrderStorageMock
	outbox *access_mocks.OutboxStorageMock
	audit  *access_mocks.AuditStorageMock
}

func newHandlerForTest(t *testing.T) (*handler, deps) {
	t.Helper()
	d := deps{
		order:  access_mocks.NewOrderStorageMock(t),
		outbox: access_mocks.NewOutboxStorageMock(t),
		audit:  access_mocks.NewAuditStorageMock(t),
	}
	h := NewHandler(HandlerConfig{
		OrderStorage:  d.order,
		OutboxStorage: d.outbox,
		AuditStorage:  d.audit,
	})
	h.now = func() time.Time { return fixedNow }
	return h, d
}

func auditOf(eventType string) interface{} {
	return mock.MatchedBy(func(e access.AuditEvent) bool { return e.EventType == eventType })
}

func sampleRequest() CreateOrderRequest {
	return CreateOrderRequest{
		ConfirmID: "11111111-1111-1111-1111-111111111111",
		Snapshot: SnapshotRequest{
			CustomerID: "member-123",
			Items: []OrderItemRequest{
				{SKU: "sku-1", Name: "Widget", Quantity: 2, PriceMinor: 500},
			},
			TotalMinor: 1000,
			Address:    "1 Market St",
		},
	}
}

func TestCreate(t *testing.T) {
	t.Run("fresh order is created, frozen snapshot, awaiting_payment, audits confirmed", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := sampleRequest()

		d.order.EXPECT().GetByConfirmID(mock.Anything, req.ConfirmID).Return(access.Order{}, access.ErrOrderNotFound)
		d.order.EXPECT().Create(mock.Anything, mock.MatchedBy(func(o access.Order) bool {
			return o.ConfirmID == req.ConfirmID &&
				o.State == access.OrderStateAwaitingPayment &&
				o.Snapshot.CustomerID == "member-123" &&
				o.Snapshot.TotalMinor == 1000 &&
				len(o.Snapshot.Items) == 1 &&
				o.OrderNo != ""
		})).RunAndReturn(func(_ context.Context, o access.Order) (access.Order, error) {
			return o, nil // storage echoes back the persisted order
		})
		d.audit.EXPECT().Append(mock.Anything, auditOf(eventOrderConfirmed)).Return(nil)

		out, err := h.create(context.Background(), req)
		r.NoError(err)
		r.Equal(access.OrderStateAwaitingPayment, out.State)
		r.Equal(req.ConfirmID, out.ConfirmID)
		r.NotEmpty(out.OrderNo)
	})

	t.Run("idempotent: existing order is returned, no Create, no audit", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := sampleRequest()
		existing := access.Order{OrderNo: "order-1", ConfirmID: req.ConfirmID, State: access.OrderStatePaid}

		d.order.EXPECT().GetByConfirmID(mock.Anything, req.ConfirmID).Return(existing, nil)

		out, err := h.create(context.Background(), req)
		r.NoError(err)
		r.Equal("order-1", out.OrderNo)
		r.Equal(access.OrderStatePaid, out.State)
	})

	t.Run("unexpected GetByConfirmID error is propagated, not treated as new", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := sampleRequest()

		d.order.EXPECT().GetByConfirmID(mock.Anything, req.ConfirmID).Return(access.Order{}, errors.New("firestore down"))

		_, err := h.create(context.Background(), req)
		r.Error(err)
		r.NotErrorIs(err, access.ErrOrderNotFound)
	})

	t.Run("create persistence failure is an error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := sampleRequest()

		d.order.EXPECT().GetByConfirmID(mock.Anything, req.ConfirmID).Return(access.Order{}, access.ErrOrderNotFound)
		d.order.EXPECT().Create(mock.Anything, mock.Anything).Return(access.Order{}, errors.New("write failed"))

		_, err := h.create(context.Background(), req)
		r.Error(err)
	})

	t.Run("audit append failure does not fail the create", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		req := sampleRequest()

		d.order.EXPECT().GetByConfirmID(mock.Anything, req.ConfirmID).Return(access.Order{}, access.ErrOrderNotFound)
		d.order.EXPECT().Create(mock.Anything, mock.Anything).RunAndReturn(
			func(_ context.Context, o access.Order) (access.Order, error) { return o, nil })
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(errors.New("audit down"))

		out, err := h.create(context.Background(), req)
		r.NoError(err) // a swallowed audit error must not break the primary outcome
		r.Equal(access.OrderStateAwaitingPayment, out.State)
	})
}
