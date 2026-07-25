import { describe, expect, it } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { renderWithProviders } from '../test/render';
import { CheckoutPage } from './CheckoutPage';
import type { ApiErrorBody } from '../api/types.gen';

const confirmLabel = /ยืนยัน|confirm/i;

interface Deferred {
  promise: Promise<void>;
  resolve: () => void;
}

function deferred(): Deferred {
  let resolve: () => void = () => {};
  const promise = new Promise<void>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

describe('CheckoutPage', () => {
  it('shows the server-computed total in a status live region', async () => {
    renderWithProviders(<CheckoutPage />, { route: '/checkout' });

    // CheckoutSummary loads the server quote and renders the total in role=status.
    const total = await screen.findByRole('status');
    // Default fixture total = 44000 minor -> ฿440.00
    expect(total).toHaveTextContent(/440\.00/);
  });

  it('disables/aria-busy the confirm in-flight, then succeeds (money path, no optimistic total)', async () => {
    const user = userEvent.setup();

    // Gate the confirm so we can observe the in-flight state.
    const gate = deferred();
    server.use(
      http.post('/api/checkout/confirm', async ({ request }) => {
        // Idempotency-Key must be present on the money path.
        expect(request.headers.get('Idempotency-Key')).toBeTruthy();
        await gate.promise;
        return HttpResponse.json({
          order: {
            order_no: 'SP-TEST-9',
            status: 'AWAITING_PAYMENT',
            total: { amount_minor: 44000, currency: 'THB' },
          },
        });
      }),
    );

    renderWithProviders(<CheckoutPage />, { route: '/checkout' });
    await screen.findByRole('status');

    await user.type(screen.getByLabelText(/ที่อยู่จัดส่ง|shipping address/i), '99/1 Bangkok');
    const confirm = screen.getByRole('button', { name: confirmLabel });
    await user.click(confirm);

    // In-flight: aria-busy + disabled (blocks double-submit).
    await waitFor(() => expect(confirm).toHaveAttribute('aria-busy', 'true'));
    expect(confirm).toBeDisabled();

    // Release and reach success: the mutation settles, aria-busy returns to
    // false and the confirm re-enables. Because the order is only created after
    // the server 200 (never optimistic), this transition only happens post-200.
    gate.resolve();
    await waitFor(() => expect(confirm).toHaveAttribute('aria-busy', 'false'));
    expect(confirm).not.toBeDisabled();
  });

  it('surfaces the coupon-expired error and does NOT auto-resubmit', async () => {
    const user = userEvent.setup();

    let confirmCalls = 0;
    server.use(
      http.post('/api/checkout/confirm', () => {
        confirmCalls += 1;
        return HttpResponse.json<ApiErrorBody>(
          { failure_mode: 'coupon_expired', message: 'coupon expired' },
          { status: 409 },
        );
      }),
    );

    renderWithProviders(<CheckoutPage />, { route: '/checkout' });
    await screen.findByRole('status');

    await user.type(screen.getByLabelText(/ที่อยู่จัดส่ง|shipping address/i), '99/1 Bangkok');
    await user.click(screen.getByRole('button', { name: confirmLabel }));

    // Neutral coupon error shows (role=alert).
    const alert = await screen.findByRole('alert');
    expect(within(alert).getByText(/คูปองนี้ใช้ไม่ได้แล้ว|no longer valid/i)).toBeInTheDocument();

    // Exactly one confirm call — the page did not auto-resubmit after the error.
    await waitFor(() => expect(confirmCalls).toBe(1));
    // Give any stray async a tick; still exactly one.
    await new Promise((r) => setTimeout(r, 50));
    expect(confirmCalls).toBe(1);
  });

  it('maps out_of_stock to its neutral microcopy on confirm', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/checkout/confirm', () =>
        HttpResponse.json<ApiErrorBody>(
          { failure_mode: 'out_of_stock', message: 'sold out' },
          { status: 409 },
        ),
      ),
    );

    renderWithProviders(<CheckoutPage />, { route: '/checkout' });
    await screen.findByRole('status');
    await user.type(screen.getByLabelText(/ที่อยู่จัดส่ง|shipping address/i), '99/1 Bangkok');
    await user.click(screen.getByRole('button', { name: confirmLabel }));

    const alert = await screen.findByRole('alert');
    expect(within(alert).getByText(/เพิ่งหมด|sold out/i)).toBeInTheDocument();
  });

  it('on a network error exposes a manual retry that reuses the same key and never auto-resubmits', async () => {
    const user = userEvent.setup();
    const seenKeys: Array<string | null> = [];
    let shouldFail = true;
    server.use(
      http.post('/api/checkout/confirm', ({ request }) => {
        seenKeys.push(request.headers.get('Idempotency-Key'));
        if (shouldFail) return HttpResponse.error();
        return HttpResponse.json({
          order: {
            order_no: 'SP-TEST-NET',
            status: 'AWAITING_PAYMENT',
            total: { amount_minor: 44000, currency: 'THB' },
          },
        });
      }),
    );

    renderWithProviders(<CheckoutPage />, { route: '/checkout' });
    await screen.findByRole('status');
    await user.type(screen.getByLabelText(/ที่อยู่จัดส่ง|shipping address/i), '99/1 Bangkok');
    await user.click(screen.getByRole('button', { name: confirmLabel }));

    // Network error surfaces a dedicated manual-retry button; one request so far.
    const retry = await screen.findByRole('button', { name: /ลองอีกครั้ง|try again/i });
    await waitFor(() => expect(seenKeys).toHaveLength(1));

    // Manual retry succeeds and reuses the SAME idempotency key.
    shouldFail = false;
    await user.click(retry);
    await waitFor(() => expect(seenKeys).toHaveLength(2));
    expect(seenKeys[0]).toBe(seenKeys[1]);
  });
});
