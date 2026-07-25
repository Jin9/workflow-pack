// Co-location rule: interface + impl + model + sentinel errors + constants in ONE file.
// CROSS-SERVICE seam: this is the gateway to the payment service provider. The
// concrete impl here is a DETERMINISTIC MOCK PSP — no real card rails — so the
// service never touches a PAN/CVV; only tokenized references cross this boundary.
package access

import (
	"context"
	"errors"
)

var (
	// ErrPaymentDeclined is returned when the PSP rejects the capture.
	ErrPaymentDeclined = errors.New("payment declined")
	// ErrPaymentTimeout is returned when the PSP does not respond in time.
	ErrPaymentTimeout = errors.New("payment timeout")
)

// PSPClient captures an authorized payment for an order. providerEventID makes the
// capture idempotent at the PSP boundary; amountMinor is the server-recorded total.
type PSPClient interface {
	Capture(ctx context.Context, orderID string, amountMinor int, providerEventID string) (CaptureResult, error)
}

type pspClient struct{}

var _ PSPClient = (*pspClient)(nil)

// NewPSPClient wires the deterministic mock PSP gateway. No PAN/CVV is ever
// accepted or stored — only the order ID, server total, and provider event ID.
func NewPSPClient() PSPClient {
	return &pspClient{}
}

// Capture is a deterministic mock: the providerEventID prefix drives the outcome so
// the seam compiles and behaves predictably without a live payment integration.
//   - "decline-*"  → ErrPaymentDeclined
//   - "timeout-*"  → ErrPaymentTimeout
//   - anything else → captured
func (c *pspClient) Capture(_ context.Context, orderID string, amountMinor int, providerEventID string) (CaptureResult, error) {
	switch {
	case hasPrefix(providerEventID, "decline-"):
		return CaptureResult{}, ErrPaymentDeclined
	case hasPrefix(providerEventID, "timeout-"):
		return CaptureResult{}, ErrPaymentTimeout
	default:
		return CaptureResult{
			OrderID:         orderID,
			AmountMinor:     amountMinor,
			ProviderEventID: providerEventID,
			Captured:        true,
		}, nil
	}
}

func hasPrefix(s, prefix string) bool {
	return len(s) >= len(prefix) && s[:len(prefix)] == prefix
}

// CaptureResult is the outcome of a successful PSP capture. It carries no PAN/CVV —
// only the order, the captured amount, and the provider's idempotency reference.
type CaptureResult struct {
	OrderID         string `json:"orderId"`
	AmountMinor     int    `json:"amountMinor"`
	ProviderEventID string `json:"providerEventId"`
	Captured        bool   `json:"captured"`
}
