package inventory_test

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"gitlab.com/example-org/platform/backend/common/app"
	"gitlab.com/example-org/platform/backend/common/wrapper"

	"gitlab.com/example-org/platform/backend/inventory/app/inventory"
	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func decodeAdjust(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[inventory.AdjustResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[inventory.AdjustResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func intPtr(n int) *int { return &n }

func TestAdjustHandler(t *testing.T) {
	const sku = "SKU-A"

	t.Run("200 on a successful adjustment", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 10).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(10), Reason: "restock"})
		h.Adjust(c)

		r.Equal(http.StatusOK, w.Code)
		resp := decodeAdjust(t, w)
		r.Equal(app.CodeSuccess, resp.Code)
		r.Equal(10, resp.Data.NewAvailable)
	})

	t.Run("200 honours an explicit zero newAvailable", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 0}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, sku, 0).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(0), Reason: "sold out"})
		h.Adjust(c)

		r.Equal(http.StatusOK, w.Code)
		r.Equal(app.CodeSuccess, decodeAdjust(t, w).Code)
	})

	t.Run("400 on missing sku", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.AdjustRequest{NewAvailable: intPtr(10), Reason: "x"})
		h.Adjust(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeAdjust(t, w).Code)
	})

	t.Run("400 on missing newAvailable", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, Reason: "x"})
		h.Adjust(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeAdjust(t, w).Code)
	})

	t.Run("400 on missing reason", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(10)})
		h.Adjust(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeAdjust(t, w).Code)
	})

	t.Run("400 when new available is below reserved", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{SKU: sku, Available: 5, Reserved: 3}, nil)

		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(2), Reason: "shrinkage"})
		h.Adjust(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeAdjust(t, w).Code)
	})

	t.Run("404 on an unknown sku", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{}, access.ErrSKUNotFound)

		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(10), Reason: "restock"})
		h.Adjust(c)

		r.Equal(http.StatusNotFound, w.Code)
		r.Equal(app.CodeNotFound, decodeAdjust(t, w).Code)
	})

	t.Run("500 on an unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.stock.EXPECT().GetBySKU(mock.Anything, sku).Return(access.Stock{}, errors.New("db down"))

		w, c := postJSON(t, inventory.AdjustRequest{SKU: sku, NewAvailable: intPtr(10), Reason: "restock"})
		h.Adjust(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeAdjust(t, w).Code)
	})
}
