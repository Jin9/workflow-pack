package checkout_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout"
	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"
	access_mocks "gitlab.com/example-org/platform/backend/checkout/app/checkout/access/mocks"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

const idemKey = "11111111-1111-1111-1111-111111111111"

// errInjected is a generic unexpected error used by external handler tests to
// drive the 500 branch.
var errInjected = errors.New("firestore down")

type mockDeps struct {
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

// checkoutAPI is the slice of the (unexported) concrete handler this external test
// exercises; *checkout.handler satisfies it, letting the helper name a return type.
type checkoutAPI interface {
	Confirm(*gin.Context)
	Capture(*gin.Context)
}

func newHandler(t *testing.T) (checkoutAPI, mockDeps) {
	t.Helper()
	d := mockDeps{
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
	h := checkout.NewHandler(checkout.HandlerConfig{
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
	return h, d
}

func postJSON(t *testing.T, body any) (*httptest.ResponseRecorder, *gin.Context) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)

	var buf bytes.Buffer
	require.NoError(t, json.NewEncoder(&buf).Encode(body))
	req := httptest.NewRequest(http.MethodPost, "http://0.0.0.0/api/v1/platform/checkout/confirm", &buf)
	req.Header.Set("Content-Type", "application/json")
	c.Request = req
	return w, c
}

func decodeConfirm(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[checkout.ConfirmResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[checkout.ConfirmResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func sampleCart() access.Cart {
	return access.Cart{
		CartID:        "cart-1",
		Items:         []access.ReserveItem{{SKU: "SKU-1", Quantity: 1}},
		SubtotalMinor: 10000,
		ShippingMinor: 500,
	}
}

func TestConfirmHandler(t *testing.T) {
	t.Run("200 on a valid confirm", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, nil)
		d.order.EXPECT().Create(mock.Anything, mock.Anything, mock.Anything).Return(access.OrderRef{OrderID: "order-1"}, nil)
		d.outbox.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)
		d.idem.EXPECT().Save(mock.Anything, mock.Anything).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", Address: "1 Market St", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeConfirm(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal("order-1", resp.Data.OrderID)
		r.Equal(10500, resp.Data.TotalMinor)
	})

	t.Run("400 on missing cartId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.ConfirmRequest{Address: "1 Market St", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeConfirm(t, w).Code)
	})

	t.Run("400 on missing address", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeConfirm(t, w).Code)
	})

	t.Run("400 on a non-uuid idempotency key", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", Address: "1 Market St", IdempotencyKey: "not-a-uuid"})
		h.Confirm(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeConfirm(t, w).Code)
	})

	t.Run("400 on out of stock", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.inventory.EXPECT().Reserve(mock.Anything, mock.Anything, mock.Anything).Return(access.ReservationRef{}, access.ErrOutOfStock)

		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", Address: "1 Market St", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeConfirm(t, w).Code)
	})

	t.Run("400 on an expired coupon", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, access.ErrIdempotencyNotFound)
		d.cart.EXPECT().GetByID(mock.Anything, "cart-1").Return(sampleCart(), nil)
		d.coupon.EXPECT().GetByCode(mock.Anything, "OLD").Return(access.Coupon{
			Code: "OLD", DiscountMinor: 1000, ExpiresAt: time.Now().Add(-time.Hour),
		}, nil)

		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", Address: "1 Market St", Coupon: "OLD", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeConfirm(t, w).Code)
	})

	t.Run("500 on an unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.idem.EXPECT().GetByKey(mock.Anything, idemKey).Return(access.IdempotencyRecord{}, errors.New("firestore down"))

		w, c := postJSON(t, checkout.ConfirmRequest{CartID: "cart-1", Address: "1 Market St", IdempotencyKey: idemKey})
		h.Confirm(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeConfirm(t, w).Code)
	})
}
