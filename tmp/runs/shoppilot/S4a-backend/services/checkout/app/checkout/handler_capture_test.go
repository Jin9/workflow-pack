package checkout_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout"
	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

const captureOrderID = "22222222-2222-2222-2222-222222222222"

func decodeCapture(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[checkout.CaptureResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[checkout.CaptureResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func TestCaptureHandler(t *testing.T) {
	t.Run("200 on a valid capture", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, "evt-1").Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, "evt-1").Return(access.CaptureResult{
			OrderID: captureOrderID, AmountMinor: 10500, Captured: true,
		}, nil)
		d.capture.EXPECT().Save(mock.Anything, mock.Anything).Return(nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, ProviderEventID: "evt-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeCapture(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.True(resp.Data.Captured)
	})

	t.Run("400 on missing orderId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.CaptureRequest{ProviderEventID: "evt-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCapture(t, w).Code)
	})

	t.Run("400 on a non-uuid orderId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.CaptureRequest{OrderID: "not-a-uuid", ProviderEventID: "evt-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCapture(t, w).Code)
	})

	t.Run("400 on missing providerEventId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCapture(t, w).Code)
	})

	t.Run("400 on amount mismatch", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, "evt-1").Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)

		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, ProviderEventID: "evt-1", Amount: 9999})
		h.Capture(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCapture(t, w).Code)
	})

	t.Run("400 on payment declined", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{}, access.ErrPaymentDeclined)

		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, ProviderEventID: "decline-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeCapture(t, w).Code)
	})

	t.Run("503 on payment timeout", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, mock.Anything).Return(access.CaptureRecord{}, access.ErrCaptureNotFound)
		d.capture.EXPECT().GetOrderTotal(mock.Anything, captureOrderID).Return(10500, nil)
		d.psp.EXPECT().Capture(mock.Anything, captureOrderID, 10500, mock.Anything).Return(access.CaptureResult{}, access.ErrPaymentTimeout)

		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, ProviderEventID: "timeout-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusServiceUnavailable, w.Code)
		r.Equal(app.CodeServiceUnavail, decodeCapture(t, w).Code)
	})

	t.Run("500 on an unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.capture.EXPECT().GetByProviderEventID(mock.Anything, "evt-1").Return(access.CaptureRecord{}, errInjected)

		w, c := postJSON(t, checkout.CaptureRequest{OrderID: captureOrderID, ProviderEventID: "evt-1", Amount: 10500})
		h.Capture(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeCapture(t, w).Code)
	})
}
