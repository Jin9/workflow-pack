package checkout

import (
	"context"
	"errors"
	"testing"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

const (
	captureOrderID = "22222222-2222-2222-2222-222222222222"
	providerEvent  = "evt-abc"
)

func captureReq(amount int, providerEventID string) CaptureRequest {
	return CaptureRequest{OrderID: captureOrderID, ProviderEventID: providerEventID, Amount: amount}
}

func TestCapture(t *testing.T) {
	t.Run("happy path validates amount, captures, saves, appends outbox, audits", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, providerEvent).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, providerEvent).Return(access.CaptureResult{
			OrderID: captureOrderID, AmountMinor: 10500, ProviderEventID: providerEvent, Captured: true,
		}, nil)
		d.capture.EXPECT().Save(mock.Anything, mock.MatchedBy(func(rec access.CaptureRecord) bool {
			return rec.ProviderEventID == providerEvent && rec.OrderID == captureOrderID && rec.Captured
		})).Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, outboxOf("order.payment.captured")).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, auditOf("order.payment.captured")).Return(nil)

		res, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.NoError(err)
		r.True(res.Captured)
		r.Equal(10500, res.AmountMinor)
	})

	t.Run("replay on the provider event id returns the prior outcome, no PSP call", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, providerEvent).Return(access.CaptureRecord{
			ProviderEventID: providerEvent, OrderID: captureOrderID, AmountMinor: 10500, Captured: true,
		}, nil)

		res, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.NoError(err)
		r.True(res.Captured)
		r.Equal(10500, res.AmountMinor)
		// No GetOrderTotal/PSP/Save/outbox/audit expected (mocks assert).
	})

	t.Run("amount mismatch is rejected before any PSP call", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, providerEvent).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)

		_, err := h.capture(context.Background(), captureReq(9999, providerEvent))

		r.ErrorIs(err, ErrAmountMismatch)
	})

	t.Run("payment declined is surfaced as ErrPaymentDeclined", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{}, access.ErrPaymentDeclined)

		_, err := h.capture(context.Background(), captureReq(10500, "decline-1"))

		r.ErrorIs(err, ErrPaymentDeclined)
	})

	t.Run("payment timeout is surfaced as ErrPaymentTimeout", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{}, access.ErrPaymentTimeout)

		_, err := h.capture(context.Background(), captureReq(10500, "timeout-1"))

		r.ErrorIs(err, ErrPaymentTimeout)
	})

	t.Run("unexpected dedupe lookup error is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, providerEvent).Return(access.CaptureRecord{}, errors.New("firestore down"))

		_, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.Error(err)
		r.NotErrorIs(err, ErrAmountMismatch)
	})

	t.Run("order total lookup failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, providerEvent).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(0, access.ErrOrderTotalNotFound)

		_, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.Error(err)
	})

	t.Run("unexpected PSP error is propagated, not masked as declined", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{}, errors.New("psp down"))

		_, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.Error(err)
		r.NotErrorIs(err, ErrPaymentDeclined)
		r.NotErrorIs(err, ErrPaymentTimeout)
	})

	t.Run("capture record save failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{
			OrderID: captureOrderID, AmountMinor: 10500, Captured: true,
		}, nil)
		d.capture.EXPECT().Save(mock.Anything, mock.Anything).Return(errors.New("save down"))

		_, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.Error(err)
	})

	t.Run("outbox append failure is propagated", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandlerForTest(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{
			OrderID: captureOrderID, AmountMinor: 10500, Captured: true,
		}, nil)
		d.capture.EXPECT().Save(mock.Anything, mock.Anything).Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(errors.New("outbox down"))

		_, err := h.capture(context.Background(), captureReq(10500, providerEvent))

		r.Error(err)
	})
}
