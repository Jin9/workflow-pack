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

const reservationID = "22222222-2222-2222-2222-222222222222"

func decodeRelease(t *testing.T, w *httptest.ResponseRecorder) wrapper.ResponseOption[inventory.ReleaseResponse] {
	t.Helper()
	var resp wrapper.ResponseOption[inventory.ReleaseResponse]
	require.NoError(t, json.NewDecoder(w.Body).Decode(&resp))
	return resp
}

func TestReleaseHandler(t *testing.T) {
	validBody := inventory.ReleaseRequest{ReservationID: reservationID, Reason: "order.cancelled"}

	t.Run("200 on a successful release", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{
			ReservationID: reservationID,
			Status:        access.ReservationStatusReserved,
			Items:         []access.ReservationItem{{SKU: "SKU-A", Qty: 2}},
		}, nil)
		d.stock.EXPECT().GetBySKU(mock.Anything, "SKU-A").Return(access.Stock{SKU: "SKU-A", Available: 8}, nil)
		d.stock.EXPECT().SetAvailable(mock.Anything, "SKU-A", 10).Return(nil)
		d.reservation.EXPECT().Release(mock.Anything, reservationID).Return(nil)
		d.audit.EXPECT().Append(mock.Anything, mock.Anything).Return(nil)

		w, c := postJSON(t, validBody)
		h.Release(c)

		r.Equal(http.StatusOK, w.Code)
		r.Equal(app.CodeSuccess, decodeRelease(t, w).Code)
	})

	t.Run("200 idempotent release of an already-released reservation", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{
			ReservationID: reservationID,
			Status:        access.ReservationStatusReleased,
		}, nil)

		w, c := postJSON(t, validBody)
		h.Release(c)

		r.Equal(http.StatusOK, w.Code)
		r.Equal(app.CodeSuccess, decodeRelease(t, w).Code)
	})

	t.Run("400 on missing reservationId", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.ReleaseRequest{Reason: "x"})
		h.Release(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeRelease(t, w).Code)
	})

	t.Run("400 on missing reason", func(t *testing.T) {
		r := require.New(t)
		h, _ := newHandler(t)
		w, c := postJSON(t, inventory.ReleaseRequest{ReservationID: reservationID})
		h.Release(c)

		r.Equal(http.StatusBadRequest, w.Code)
		r.Equal(app.CodeBadRequest, decodeRelease(t, w).Code)
	})

	t.Run("404 on an unknown reservation", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, access.ErrReservationNotFound)

		w, c := postJSON(t, validBody)
		h.Release(c)

		r.Equal(http.StatusNotFound, w.Code)
		r.Equal(app.CodeNotFound, decodeRelease(t, w).Code)
	})

	t.Run("500 on an unexpected storage error", func(t *testing.T) {
		r := require.New(t)
		h, d := newHandler(t)
		d.reservation.EXPECT().GetByID(mock.Anything, reservationID).Return(access.Reservation{}, errors.New("firestore down"))

		w, c := postJSON(t, validBody)
		h.Release(c)

		r.Equal(http.StatusInternalServerError, w.Code)
		r.Equal(app.CodeInternalError, decodeRelease(t, w).Code)
	})
}
