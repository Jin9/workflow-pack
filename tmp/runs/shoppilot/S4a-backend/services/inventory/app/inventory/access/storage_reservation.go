// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"errors"
	"fmt"
	"time"

	gcpfirestore "cloud.google.com/go/firestore"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ErrReservationNotFound is returned when no reservation matches the lookup key.
var ErrReservationNotFound = errors.New("reservation not found")

// ReservationStorage owns the reservation lifecycle. GetByConfirmID gives the
// reserve path idempotency (a repeated confirmId returns the existing
// reservation rather than decrementing again, ADR-004).
type ReservationStorage interface {
	GetByConfirmID(ctx context.Context, confirmID string) (Reservation, error)
	Create(ctx context.Context, reservation Reservation) (Reservation, error)
	GetByID(ctx context.Context, id string) (Reservation, error)
	Release(ctx context.Context, id string) error
}

type reservationStorage struct {
	fs *gcpfirestore.Client
}

var _ ReservationStorage = (*reservationStorage)(nil)

const (
	reservationCollection  = "reservations"
	confirmIndexCollection = "reservation_confirm_index"
)

// Reservation status values. A reservation is released exactly once; the
// compensation (release) path is idempotent on this field.
const (
	ReservationStatusReserved = "reserved"
	ReservationStatusReleased = "released"
)

// NewReservationStorage wires the reservation repository over Firestore.
func NewReservationStorage(fs *gcpfirestore.Client) ReservationStorage {
	return &reservationStorage{fs: fs}
}

func (s *reservationStorage) GetByConfirmID(ctx context.Context, confirmID string) (Reservation, error) {
	idxDoc, err := s.fs.Collection(confirmIndexCollection).Doc(confirmID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Reservation{}, ErrReservationNotFound
		}
		return Reservation{}, fmt.Errorf("failed to resolve confirm id index: %w", err)
	}

	var idx confirmIDIndex
	if err := idxDoc.DataTo(&idx); err != nil {
		return Reservation{}, fmt.Errorf("failed to parse confirm id index: %w", err)
	}

	return s.GetByID(ctx, idx.ReservationID)
}

func (s *reservationStorage) Create(ctx context.Context, reservation Reservation) (Reservation, error) {
	now := time.Now().UTC()
	reservation.CreatedAt = now
	reservation.UpdatedAt = now

	if _, err := s.fs.Collection(reservationCollection).Doc(reservation.ReservationID).Set(ctx, reservation); err != nil {
		return Reservation{}, fmt.Errorf("failed to create reservation: %w", err)
	}
	if _, err := s.fs.Collection(confirmIndexCollection).Doc(reservation.ConfirmID).Set(ctx, confirmIDIndex{ReservationID: reservation.ReservationID}); err != nil {
		return Reservation{}, fmt.Errorf("failed to index reservation confirm id: %w", err)
	}
	return reservation, nil
}

func (s *reservationStorage) GetByID(ctx context.Context, id string) (Reservation, error) {
	doc, err := s.fs.Collection(reservationCollection).Doc(id).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Reservation{}, ErrReservationNotFound
		}
		return Reservation{}, fmt.Errorf("failed to get reservation: %w", err)
	}

	var entity Reservation
	if err := doc.DataTo(&entity); err != nil {
		return Reservation{}, fmt.Errorf("failed to parse reservation: %w", err)
	}
	return entity, nil
}

func (s *reservationStorage) Release(ctx context.Context, id string) error {
	updates := []gcpfirestore.Update{
		{Path: "status", Value: ReservationStatusReleased},
		{Path: "updated_at", Value: time.Now().UTC()},
	}
	if _, err := s.fs.Collection(reservationCollection).Doc(id).Update(ctx, updates); err != nil {
		if status.Code(err) == codes.NotFound {
			return ErrReservationNotFound
		}
		return fmt.Errorf("failed to release reservation: %w", err)
	}
	return nil
}

type confirmIDIndex struct {
	ReservationID string `firestore:"reservation_id" json:"reservationId"`
}

// ReservationItem is one SKU/quantity line held by a reservation.
type ReservationItem struct {
	SKU string `firestore:"sku" json:"sku"`
	Qty int    `firestore:"qty" json:"qty"`
}

// Reservation holds stock against an in-flight order. ExpiresAt drives the 30m
// TTL compensation (ADR-004): if the order is never confirmed, the reservation
// is released and the held stock returns to available.
type Reservation struct {
	ReservationID string            `firestore:"reservation_id" json:"reservationId"`
	ConfirmID     string            `firestore:"confirm_id" json:"confirmId"`
	Items         []ReservationItem `firestore:"items" json:"items"`
	Status        string            `firestore:"status" json:"status"`
	ExpiresAt     time.Time         `firestore:"expires_at" json:"expiresAt"`
	CreatedAt     time.Time         `firestore:"created_at" json:"createdAt"`
	UpdatedAt     time.Time         `firestore:"updated_at" json:"updatedAt"`
}
