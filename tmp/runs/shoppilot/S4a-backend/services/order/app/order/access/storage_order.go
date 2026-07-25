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

// ErrOrderNotFound is returned when no order matches the lookup key
// (confirmId for idempotency or orderNo for reads/transitions).
var ErrOrderNotFound = errors.New("order not found")

// Order state machine values. Forward-only happy path plus terminal failures.
const (
	OrderStateAwaitingPayment = "awaiting_payment"
	OrderStatePaid            = "paid"
	OrderStatePacking         = "packing"
	OrderStateShipped         = "shipped"
	OrderStateDelivered       = "delivered"
	OrderStatePaymentFailed   = "payment_failed"
	OrderStatePaymentTimeout  = "payment_timeout"
	OrderStateCancelled       = "cancelled"
)

// OrderStorage owns the order aggregate. Create is idempotent at the service
// layer via GetByConfirmID; reads resolve by the public order number; UpdateState
// advances the forward-only state machine and (for shipped) records the tracking number.
type OrderStorage interface {
	GetByConfirmID(ctx context.Context, confirmID string) (Order, error)
	Create(ctx context.Context, order Order) (Order, error)
	GetByOrderNo(ctx context.Context, orderNo string) (Order, error)
	UpdateState(ctx context.Context, orderNo, state, trackingNo string) error
}

type orderStorage struct {
	fs *gcpfirestore.Client
}

var _ OrderStorage = (*orderStorage)(nil)

const (
	orderCollection        = "orders"
	confirmIndexCollection = "order_confirm_index"
)

// NewOrderStorage wires the order repository over Firestore.
func NewOrderStorage(fs *gcpfirestore.Client) OrderStorage {
	return &orderStorage{fs: fs}
}

func (s *orderStorage) GetByConfirmID(ctx context.Context, confirmID string) (Order, error) {
	idxDoc, err := s.fs.Collection(confirmIndexCollection).Doc(confirmID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Order{}, ErrOrderNotFound
		}
		return Order{}, fmt.Errorf("failed to resolve confirm id index: %w", err)
	}

	var idx confirmIndex
	if err := idxDoc.DataTo(&idx); err != nil {
		return Order{}, fmt.Errorf("failed to parse confirm id index: %w", err)
	}

	return s.GetByOrderNo(ctx, idx.OrderNo)
}

func (s *orderStorage) Create(ctx context.Context, order Order) (Order, error) {
	now := time.Now().UTC()
	order.CreatedAt = now
	order.UpdatedAt = now

	if _, err := s.fs.Collection(orderCollection).Doc(order.OrderNo).Set(ctx, order); err != nil {
		return Order{}, fmt.Errorf("failed to create order: %w", err)
	}
	if _, err := s.fs.Collection(confirmIndexCollection).Doc(order.ConfirmID).Set(ctx, confirmIndex{OrderNo: order.OrderNo}); err != nil {
		return Order{}, fmt.Errorf("failed to index confirm id: %w", err)
	}
	return order, nil
}

func (s *orderStorage) GetByOrderNo(ctx context.Context, orderNo string) (Order, error) {
	doc, err := s.fs.Collection(orderCollection).Doc(orderNo).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Order{}, ErrOrderNotFound
		}
		return Order{}, fmt.Errorf("failed to get order by order no: %w", err)
	}

	var order Order
	if err := doc.DataTo(&order); err != nil {
		return Order{}, fmt.Errorf("failed to parse order data: %w", err)
	}
	return order, nil
}

func (s *orderStorage) UpdateState(ctx context.Context, orderNo, state, trackingNo string) error {
	updates := []gcpfirestore.Update{
		{Path: "state", Value: state},
		{Path: "updated_at", Value: time.Now().UTC()},
	}
	if trackingNo != "" {
		updates = append(updates, gcpfirestore.Update{Path: "tracking_no", Value: trackingNo})
	}
	if _, err := s.fs.Collection(orderCollection).Doc(orderNo).Update(ctx, updates); err != nil {
		return fmt.Errorf("failed to update order state: %w", err)
	}
	return nil
}

type confirmIndex struct {
	OrderNo string `firestore:"order_no" json:"orderNo"`
}

// OrderItem is one line of the frozen snapshot.
type OrderItem struct {
	SKU       string `firestore:"sku" json:"sku"`
	Name      string `firestore:"name" json:"name"`
	Quantity  int    `firestore:"quantity" json:"quantity"`
	PriceMinor int   `firestore:"price_minor" json:"priceMinor"`
}

// Snapshot is the IMMUTABLE record of what the customer confirmed (ADR-003).
// It is frozen at order creation and never mutated; state changes live on Order.
type Snapshot struct {
	CustomerID string      `firestore:"customer_id" json:"customerId"`
	Items      []OrderItem `firestore:"items" json:"items"`
	TotalMinor int         `firestore:"total_minor" json:"totalMinor"`
	Address    string      `firestore:"address" json:"address"`
}

// Order is the order aggregate. Snapshot is immutable; State, TrackingNo and the
// timestamps are the only mutable fields and only advance via the state machine.
type Order struct {
	OrderNo    string    `firestore:"order_no" json:"orderNo"`
	ConfirmID  string    `firestore:"confirm_id" json:"confirmId"`
	Snapshot   Snapshot  `firestore:"snapshot" json:"snapshot"`
	State      string    `firestore:"state" json:"state"`
	TrackingNo string    `firestore:"tracking_no" json:"trackingNo"`
	CreatedAt  time.Time `firestore:"created_at" json:"createdAt"`
	UpdatedAt  time.Time `firestore:"updated_at" json:"updatedAt"`
}
