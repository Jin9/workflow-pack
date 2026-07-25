// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"errors"
	"fmt"

	gcpfirestore "cloud.google.com/go/firestore"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ErrCartNotFound is returned when no cart matches the cart ID.
var ErrCartNotFound = errors.New("cart not found")

// CartStorage provides the SERVER-trusted cart snapshot (line items, subtotal,
// shipping) at confirm time. These figures — never client-supplied ones — feed the
// pure total computation, so the total cannot be forged by the caller.
type CartStorage interface {
	GetByID(ctx context.Context, cartID string) (Cart, error)
}

type cartStorage struct {
	fs *gcpfirestore.Client
}

var _ CartStorage = (*cartStorage)(nil)

const cartCollection = "carts"

// NewCartStorage wires the cart repository over Firestore.
func NewCartStorage(fs *gcpfirestore.Client) CartStorage {
	return &cartStorage{fs: fs}
}

func (s *cartStorage) GetByID(ctx context.Context, cartID string) (Cart, error) {
	doc, err := s.fs.Collection(cartCollection).Doc(cartID).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Cart{}, ErrCartNotFound
		}
		return Cart{}, fmt.Errorf("failed to get cart by id: %w", err)
	}

	var entity Cart
	if err := doc.DataTo(&entity); err != nil {
		return Cart{}, fmt.Errorf("failed to parse cart data: %w", err)
	}
	return entity, nil
}

// Cart is the server-side basket. SubtotalMinor and ShippingMinor are the trusted
// money figures; Items is the reservation list. All amounts are minor currency units.
type Cart struct {
	CartID        string        `firestore:"cart_id" json:"cartId"`
	Items         []ReserveItem `firestore:"items" json:"items"`
	SubtotalMinor int           `firestore:"subtotal_minor" json:"subtotalMinor"`
	ShippingMinor int           `firestore:"shipping_minor" json:"shippingMinor"`
}
