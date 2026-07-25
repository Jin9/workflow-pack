// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
package access

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
)

var (
	// ErrSKUNotFound is returned when no stock row exists for the SKU.
	ErrSKUNotFound = errors.New("sku not found")
	// ErrInsufficientStock is returned when the available quantity cannot cover
	// the requested decrement (the atomic UPDATE matched the row but the
	// available >= qty guard failed).
	ErrInsufficientStock = errors.New("insufficient stock")
	// ErrBelowReserved is returned when an adjustment would set available below
	// the quantity already reserved (an invariant the inventory must never break).
	ErrBelowReserved = errors.New("new available is below reserved quantity")
)

// StockStorage owns per-SKU on-hand quantities. ConditionalDecrement is the
// ADR-002 atomic guard: a single parameterized UPDATE ... WHERE available >= qty,
// so concurrent reservations can never oversell.
type StockStorage interface {
	GetBySKU(ctx context.Context, sku string) (Stock, error)
	ConditionalDecrement(ctx context.Context, sku string, qty int) (int, error)
	SetAvailable(ctx context.Context, sku string, n int) error
}

type stockStorage struct {
	db *sql.DB
}

var _ StockStorage = (*stockStorage)(nil)

const stockTable = "stock"

// NewStockStorage wires the stock repository over MySQL.
func NewStockStorage(db *sql.DB) StockStorage {
	return &stockStorage{db: db}
}

func (s *stockStorage) GetBySKU(ctx context.Context, sku string) (Stock, error) {
	const query = "SELECT sku, available, reserved FROM " + stockTable + " WHERE sku = ?"
	row := s.db.QueryRowContext(ctx, query, sku)

	var entity Stock
	if err := row.Scan(&entity.SKU, &entity.Available, &entity.Reserved); err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return Stock{}, ErrSKUNotFound
		}
		return Stock{}, fmt.Errorf("failed to get stock by sku: %w", err)
	}
	return entity, nil
}

// ConditionalDecrement atomically moves qty from available to reserved when, and
// only when, available >= qty (ADR-002 single parameterized UPDATE). A zero
// rows-affected result means either the SKU is absent or the guard failed; a
// follow-up existence check disambiguates ErrSKUNotFound from ErrInsufficientStock.
// Returns the remaining available quantity after the decrement.
func (s *stockStorage) ConditionalDecrement(ctx context.Context, sku string, qty int) (int, error) {
	const update = "UPDATE " + stockTable +
		" SET available = available - ?, reserved = reserved + ? WHERE sku = ? AND available >= ?"
	res, err := s.db.ExecContext(ctx, update, qty, qty, sku, qty)
	if err != nil {
		return 0, fmt.Errorf("failed to conditionally decrement stock: %w", err)
	}

	affected, err := res.RowsAffected()
	if err != nil {
		return 0, fmt.Errorf("failed to read rows affected: %w", err)
	}

	if affected == 0 {
		current, err := s.GetBySKU(ctx, sku)
		if err != nil {
			return 0, err
		}
		return current.Available, ErrInsufficientStock
	}

	updated, err := s.GetBySKU(ctx, sku)
	if err != nil {
		return 0, err
	}
	return updated.Available, nil
}

// SetAvailable overwrites the available quantity for a SKU (the adjust path).
func (s *stockStorage) SetAvailable(ctx context.Context, sku string, n int) error {
	const update = "UPDATE " + stockTable + " SET available = ? WHERE sku = ?"
	res, err := s.db.ExecContext(ctx, update, n, sku)
	if err != nil {
		return fmt.Errorf("failed to set available stock: %w", err)
	}
	affected, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to read rows affected: %w", err)
	}
	if affected == 0 {
		return ErrSKUNotFound
	}
	return nil
}

// Stock is the on-hand record for a single SKU. Available is sellable; Reserved
// is held against in-flight orders. Their sum is the physical on-hand count.
type Stock struct {
	SKU       string `json:"sku"`
	Available int    `json:"available"`
	Reserved  int    `json:"reserved"`
}
