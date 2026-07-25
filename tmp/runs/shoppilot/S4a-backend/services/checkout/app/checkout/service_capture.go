package checkout

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"

	"gitlab.com/example-org/platform/backend/common/serror"

	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/google/uuid"
)

var (
	// ErrAmountMismatch is returned when the claimed capture amount disagrees with
	// the server-recorded order total. The PSP is never called in that case.
	ErrAmountMismatch = errors.New("amount mismatch")
	// ErrPaymentDeclined re-exposes the PSP decline at the domain layer.
	ErrPaymentDeclined = access.ErrPaymentDeclined
	// ErrPaymentTimeout re-exposes the PSP timeout at the domain layer.
	ErrPaymentTimeout = access.ErrPaymentTimeout
)

const eventOrderPaymentCaptured = "order.payment.captured"

type captureResult struct {
	OrderID     string
	AmountMinor int
	Captured    bool
}

// capture settles a payment (A2 idempotency, ADR-008 outbox, ADR-006 audit):
//  1. dedupe on providerEventID — a replay returns the prior outcome, no PSP call.
//  2. amount check — a claimed amount != the server total is rejected, no PSP call.
//  3. PSP capture — declined → ErrPaymentDeclined; timeout → ErrPaymentTimeout.
//  4. persist the capture record, append order.payment.captured to the outbox.
//  5. audit order.payment.captured.
func (h *handler) capture(ctx context.Context, req CaptureRequest) (captureResult, error) {
	// 1) Replay dedupe.
	if prior, err := h.captureStorage.GetByProviderEventID(ctx, req.ProviderEventID); err == nil {
		return captureResult{OrderID: prior.OrderID, AmountMinor: prior.AmountMinor, Captured: prior.Captured}, nil
	} else if !errors.Is(err, access.ErrCaptureNotFound) {
		return captureResult{}, serror.Wrap(err).With(slog.String("provider_event_id", req.ProviderEventID))
	}

	// 2) Validate the amount against the server-recorded total.
	serverTotal, err := h.captureStorage.GetOrderTotal(ctx, req.OrderID)
	if err != nil {
		return captureResult{}, serror.Wrap(err).With(slog.String("order_id", req.OrderID))
	}
	if req.Amount != serverTotal {
		return captureResult{}, ErrAmountMismatch
	}

	// 3) PSP capture (mock PSP — no PAN/CVV).
	res, err := h.pspClient.Capture(ctx, req.OrderID, req.Amount, req.ProviderEventID)
	if err != nil {
		if errors.Is(err, access.ErrPaymentDeclined) {
			return captureResult{}, ErrPaymentDeclined
		}
		if errors.Is(err, access.ErrPaymentTimeout) {
			return captureResult{}, ErrPaymentTimeout
		}
		return captureResult{}, serror.Wrap(err).With(slog.String("order_id", req.OrderID))
	}

	// 4) Persist + outbox.
	rec := access.CaptureRecord{
		ProviderEventID: req.ProviderEventID,
		OrderID:         req.OrderID,
		AmountMinor:     res.AmountMinor,
		Captured:        res.Captured,
		CreatedAt:       h.now(),
	}
	if err := h.captureStorage.Save(ctx, rec); err != nil {
		return captureResult{}, serror.Wrap(err).With(slog.String("order_id", req.OrderID))
	}
	if err := h.appendPaymentCaptured(ctx, req.OrderID, res.AmountMinor); err != nil {
		return captureResult{}, serror.Wrap(err).With(slog.String("order_id", req.OrderID))
	}

	// 5) Audit.
	h.audit(ctx, eventOrderPaymentCaptured, req.OrderID)

	return captureResult{OrderID: req.OrderID, AmountMinor: res.AmountMinor, Captured: res.Captured}, nil
}

func (h *handler) appendPaymentCaptured(ctx context.Context, orderID string, amountMinor int) error {
	payload, err := json.Marshal(map[string]any{"orderId": orderID, "amountMinor": amountMinor})
	if err != nil {
		return fmt.Errorf("failed to encode outbox payload: %w", err)
	}
	ev := access.OutboxEvent{
		EventID:     uuid.NewString(),
		EventType:   eventOrderPaymentCaptured,
		AggregateID: orderID,
		Payload:     string(payload),
		CreatedAt:   h.now(),
	}
	if err := h.outboxStorage.Append(ctx, ev); err != nil {
		return fmt.Errorf("failed to append payment-captured outbox event: %w", err)
	}
	return nil
}
