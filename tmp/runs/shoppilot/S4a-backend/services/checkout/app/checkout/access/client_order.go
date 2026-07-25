// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
// CROSS-SERVICE seam: this is an HTTP gateway to the order service. It MUST NOT
// import the order service's Go packages — the contract is HTTP only.
package access

import (
	"context"
	"fmt"
	"net/http"

	"gitlab.com/example-org/platform/backend/common/httpclient"
)

// OrderClient creates the durable order record after stock is reserved (ADR-007
// sync orchestration: reserve→create runs inline in the confirm flow).
type OrderClient interface {
	Create(ctx context.Context, confirmID string, snapshot OrderSnapshot) (OrderRef, error)
}

type orderClient struct {
	httpClient *http.Client
	baseURL    string
}

var _ OrderClient = (*orderClient)(nil)

const orderCreatePath = "/api/v1/platform/order/create"

// NewOrderClient wires the order HTTP gateway.
func NewOrderClient(httpClient *http.Client, baseURL string) OrderClient {
	return &orderClient{httpClient: httpClient, baseURL: baseURL}
}

func (c *orderClient) Create(ctx context.Context, confirmID string, snapshot OrderSnapshot) (OrderRef, error) {
	req := createOrderRequest{ConfirmID: confirmID, Snapshot: snapshot}
	resp, err := httpclient.Post[createOrderRequest, createOrderResponse](ctx, c.httpClient, c.baseURL+orderCreatePath, req)
	if err != nil {
		return OrderRef{}, fmt.Errorf("failed to call order create: %w", err)
	}
	if resp.Code != http.StatusOK && resp.Code != http.StatusCreated {
		return OrderRef{}, fmt.Errorf("order create returned status %d", resp.Code)
	}
	return OrderRef{OrderID: resp.Response.OrderID}, nil
}

type createOrderRequest struct {
	ConfirmID string        `json:"confirmId"`
	Snapshot  OrderSnapshot `json:"snapshot"`
}

type createOrderResponse struct {
	OrderID string `json:"orderId"`
}

// OrderSnapshot is the server-computed, trusted order state handed to the order
// service. TotalMinor is the authoritative total computed by checkout, never the client.
type OrderSnapshot struct {
	CartID        string        `json:"cartId"`
	Address       string        `json:"address"`
	Items         []ReserveItem `json:"items"`
	SubtotalMinor int           `json:"subtotalMinor"`
	DiscountMinor int           `json:"discountMinor"`
	ShippingMinor int           `json:"shippingMinor"`
	TotalMinor    int           `json:"totalMinor"`
}

// OrderRef is the handle to a created order.
type OrderRef struct {
	OrderID string `json:"orderId"`
}
