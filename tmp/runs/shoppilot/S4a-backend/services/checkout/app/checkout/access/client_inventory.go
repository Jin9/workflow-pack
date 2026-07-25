// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
// CROSS-SERVICE seam: this is an HTTP gateway to the inventory service. It MUST
// NOT import the inventory service's Go packages — the contract is HTTP only.
package access

import (
	"context"
	"errors"
	"fmt"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/httpclient"
)

// ErrOutOfStock is returned when inventory cannot reserve all requested items.
var ErrOutOfStock = errors.New("out of stock")

// InventoryClient reserves stock for a confirm attempt (ADR-007 sync orchestration:
// the checkout service drives reserve→create-order inline, with no standalone orchestrator).
type InventoryClient interface {
	Reserve(ctx context.Context, confirmID string, items []ReserveItem) (ReservationRef, error)
}

type inventoryClient struct {
	httpClient *http.Client
	baseURL    string
}

var _ InventoryClient = (*inventoryClient)(nil)

const inventoryReservePath = "/api/v1/platform/inventory/reserve"

// NewInventoryClient wires the inventory HTTP gateway.
func NewInventoryClient(httpClient *http.Client, baseURL string) InventoryClient {
	return &inventoryClient{httpClient: httpClient, baseURL: baseURL}
}

func (c *inventoryClient) Reserve(ctx context.Context, confirmID string, items []ReserveItem) (ReservationRef, error) {
	req := reserveRequest{ConfirmID: confirmID, Items: items}
	resp, err := httpclient.Post[reserveRequest, reserveResponse](ctx, c.httpClient, c.baseURL+inventoryReservePath, req)
	if err != nil {
		return ReservationRef{}, fmt.Errorf("failed to call inventory reserve: %w", err)
	}
	if resp.Code == http.StatusConflict {
		return ReservationRef{}, ErrOutOfStock
	}
	if resp.Code != http.StatusOK {
		return ReservationRef{}, fmt.Errorf("inventory reserve returned status %d", resp.Code)
	}
	return ReservationRef{ReservationID: resp.Response.ReservationID}, nil
}

type reserveRequest struct {
	ConfirmID string        `json:"confirmId"`
	Items     []ReserveItem `json:"items"`
}

type reserveResponse struct {
	ReservationID string `json:"reservationId"`
}

// ReserveItem is one line-item to reserve (SKU + quantity).
type ReserveItem struct {
	SKU      string `json:"sku"`
	Quantity int    `json:"quantity"`
}

// ReservationRef is the handle to a successful stock reservation.
type ReservationRef struct {
	ReservationID string `json:"reservationId"`
}
