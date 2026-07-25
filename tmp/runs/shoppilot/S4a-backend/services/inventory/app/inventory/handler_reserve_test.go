package inventory_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory"
	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"
	access_mocks "gitlab.com/example-org/platform/backend/inventory/app/inventory/access/mocks"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

const confirmID = "11111111-1111-1111-1111-111111111111"

// inventoryAPI is the slice of the (unexported) concrete handler the external
// tests exercise; *inventory.handler satisfies it, letting the helper name a type.
type inventoryAPI interface {
	Reserve(*gin.Context)
	Release(*gin.Context)
	Adjust(*gin.Context)
}

type mockDeps struct {
	stock       *access_mocks.StockStorageMock
	reservation *access_mocks.ReservationStorageMock
	audit       *access_mocks.AuditStorageMock
}

func newHandler(t *testing.T) (inventoryAPI, mockDeps) {
	t.Helper()
	d := mockDeps{
		stock:       access_mocks.NewStockStorageMock(t),
		reservation: access_mocks.NewReservationStorageMock(t),
		audit:       access_mocks.NewAuditStorageMock(t),
	}
	h := inventory.NewHandler(inventory.HandlerConfig{
		StockStorage:       d.stock,
		ReservationStorage: d.reservation,
		AuditStorage:       d.audit,
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
	req := httptest.NewRequest(http.MethodPost, "http://0.0.0.0/api/v1/platform/inventory/reserve", &buf)
	req.Header.Set("Content-Type", "application/json")
	c.Request = req
	return w, c
}

func decodeReserve(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[inventory.ReserveResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[inventory.ReserveResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func TestReserveHandler(t *testing.T) {
	validBody := inventory.ReserveRequest{
		ConfirmID: confirmID,
		Items:     []inventory.ReserveItem{{SKU: "SKU-A", Qty: 2}},
	}

	t.Run("200 on a successful reservation", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(8, nil)
		d.reservation.EXPECT().Create(mock.Anything, mock.Anything).Return(access.Reservation{ReservationID: "res-1"}, nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, validBody)
		h.Reserve(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeReserve(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal("res-1", resp.Data.ReservationID)
	})

	t.Run("400 on missing confirmId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.ReserveRequest{Items: validBody.Items})
		h.Reserve(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeReserve(t, w).Code)
	})

	t.Run("400 on a non-uuid confirmId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.ReserveRequest{ConfirmID: "not-a-uuid", Items: validBody.Items})
		h.Reserve(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeReserve(t, w).Code)
	})

	t.Run("400 on empty items", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.ReserveRequest{ConfirmID: confirmID, Items: []inventory.ReserveItem{}})
		h.Reserve(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeReserve(t, w).Code)
	})

	t.Run("400 on insufficient stock", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(1, access.ErrInsufficientStock)

		w, c := postJSON(t, validBody)
		h.Reserve(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeReserve(t, w).Code)
	})

	t.Run("404 on an unknown sku", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, access.ErrReservationNotFound)
		d.stock.EXPECT().ConditionalDecrement(mock.Anything, "SKU-A", 2).Return(0, access.ErrSKUNotFound)

		w, c := postJSON(t, validBody)
		h.Reserve(c)

		r.Equal(http.StatusNotFound, w.Code)
		r.Equal(app.CodeNotFound, decodeReserve(t, w).Code)
	})

	t.Run("500 on an unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByConfirmID(mock.Anything, confirmID).Return(access.Reservation{}, errors.New("firestore down"))

		w, c := postJSON(t, validBody)
		h.Reserve(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeReserve(t, w).Code)
	})
}
