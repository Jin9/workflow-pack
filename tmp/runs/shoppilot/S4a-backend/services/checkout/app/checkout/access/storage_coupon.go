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

// ErrCouponNotFound is returned when no coupon matches the presented code.
var ErrCouponNotFound = errors.New("coupon not found")

// CouponStorage resolves a coupon by its public code so the service layer can
// re-validate the discount server-side (a client-supplied total is never trusted).
type CouponStorage interface {
	GetByCode(ctx context.Context, code string) (Coupon, error)
}

type couponStorage struct {
	fs *gcpfirestore.Client
}

var _ CouponStorage = (*couponStorage)(nil)

const couponCollection = "coupons"

// NewCouponStorage wires the coupon repository over Firestore.
func NewCouponStorage(fs *gcpfirestore.Client) CouponStorage {
	return &couponStorage{fs: fs}
}

func (s *couponStorage) GetByCode(ctx context.Context, code string) (Coupon, error) {
	doc, err := s.fs.Collection(couponCollection).Doc(code).Get(ctx)
	if err != nil {
		if status.Code(err) == codes.NotFound {
			return Coupon{}, ErrCouponNotFound
		}
		return Coupon{}, fmt.Errorf("failed to get coupon by code: %w", err)
	}

	var entity Coupon
	if err := doc.DataTo(&entity); err != nil {
		return Coupon{}, fmt.Errorf("failed to parse coupon data: %w", err)
	}
	return entity, nil
}

// Coupon is the stored discount record. DiscountMinor is the absolute discount in
// minor currency units; ExpiresAt bounds the validity window (re-checked at confirm).
type Coupon struct {
	Code         string    `firestore:"code" json:"code"`
	DiscountMinor int      `firestore:"discount_minor" json:"discountMinor"`
	ExpiresAt    time.Time `firestore:"expires_at" json:"expiresAt"`
}
