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

// ErrCaptureNotFound is returned when no capture matches the provider event ID.
var ErrCaptureNotFound = errors.New("capture not found")

// CaptureStorage is the payment-capture ledger. It dedupes PSP webhooks on the
// provider event ID (replay returns the prior outcome) and records the server
// total per order so a capture amount can be validated against the trusted figure.
type CaptureStorage interface {
	GetByProviderEventID(ctx context.Context, providerEventID string) (CaptureRecord, error)
	GetOrderTotal(ctx context.Context, orderID string) (int, error)
	Save(ctx context.Context, record CaptureRecord) error
}

type captureStorage struct {
	fs *gcpfirestore.Client
}

var _ CaptureStorage = (*captureStorage)(nil)

const (
	captureCollection    = "checkout_captures"
	orderTotalCollection = "checkout_order_totals"
)

// NewCaptureStorage wires the capture ledger over Firestore.
func NewCaptureStorage(fs *gcpfirestore.Client) CaptureStorage {
	return &captureStorage{fs: fs}
}

func (s *captureStorage) GetByProviderEventID(ctx context.Context, providerEventID string) (CaptureRecord, error) {
	doc, err := s.fs.Collection(captureCollection).Doc(providerEventID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return CaptureRecord{}, ErrCaptureNotFound
		}
		return CaptureRecord{}, fmt.Errorf("failed to get capture record: %w", err)
	}

	var entity CaptureRecord
	if err := doc.DataTo(&entity); err != nil {
		return CaptureRecord{}, fmt.Errorf("failed to parse capture record: %w", err)
	}
	return entity, nil
}

func (s *captureStorage) GetOrderTotal(ctx context.Context, orderID string) (int, error) {
	doc, err := s.fs.Collection(orderTotalCollection).Doc(orderID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return 0, ErrOrderTotalNotFound
		}
		return 0, fmt.Errorf("failed to get order total: %w", err)
	}

	var entity orderTotal
	if err := doc.DataTo(&entity); err != nil {
		return 0, fmt.Errorf("failed to parse order total: %w", err)
	}
	return entity.TotalMinor, nil
}

func (s *captureStorage) Save(ctx context.Context, record CaptureRecord) error {
	if record.CreatedAt.IsZero() {
		record.CreatedAt = time.Now().UTC()
	}
	if _, err := s.fs.Collection(captureCollection).Doc(record.ProviderEventID).Set(ctx, record); err != nil {
		return fmt.Errorf("failed to save capture record: %w", err)
	}
	return nil
}

// ErrOrderTotalNotFound is returned when no server total is recorded for an order.
var ErrOrderTotalNotFound = errors.New("order total not found")

type orderTotal struct {
	OrderID    string `firestore:"order_id" json:"orderId"`
	TotalMinor int    `firestore:"total_minor" json:"totalMinor"`
}

// CaptureRecord is one settled (or attempted) payment capture, deduped on
// ProviderEventID. No PAN/CVV is stored — only the order, amount, and outcome.
type CaptureRecord struct {
	ProviderEventID string    `firestore:"provider_event_id" json:"providerEventId"`
	OrderID         string    `firestore:"order_id" json:"orderId"`
	AmountMinor     int       `firestore:"amount_minor" json:"amountMinor"`
	Captured        bool      `firestore:"captured" json:"captured"`
	CreatedAt       time.Time `firestore:"created_at" json:"createdAt"`
}
