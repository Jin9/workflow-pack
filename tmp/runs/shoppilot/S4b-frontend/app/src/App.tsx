import { type ReactNode, useState } from 'react';
import { Navigate, Route, Routes, useSearchParams, NavLink } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { LoginPage } from './pages/LoginPage';
import { CheckoutPage } from './pages/CheckoutPage';
import { OrdersPage } from './pages/OrdersPage';
import { OrderDetailPage } from './pages/OrderDetailPage';
import { PaymentPanel, type PaymentStatus } from './features/checkout/PaymentPanel';
import { ApiError, captureCheckout } from './api/client';
import type { CheckoutCaptureResponse } from './api/types.gen';
import { generateIdempotencyKey } from './hooks/useIdempotentConfirm';
import { useT } from './i18n/microcopy';

/*
 * App — route shell. active_route is URL-owned (router). Catalog/cart routes
 * from the route-map are intentionally NOT realized (outside the manifest's
 * 4-page surface); the shell redirects "/" to the orders surface.
 */
export function App(): ReactNode {
  const tr = useT();
  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-title">ShopPilot</span>
        <nav className="app-nav" aria-label={tr('screen.orders.title')}>
          <NavLink to="/orders">{tr('nav.tab.orders')}</NavLink>
          <NavLink to="/login">{tr('common.action.login')}</NavLink>
        </nav>
      </header>

      <Routes>
        <Route path="/" element={<Navigate to="/orders" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/checkout/payment" element={<PaymentRoute />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/orders/:orderNo" element={<OrderDetailPage />} />
        <Route path="*" element={<Navigate to="/orders" replace />} />
      </Routes>
    </div>
  );
}

/*
 * PaymentRoute — thin route host for the PaymentPanel feature (not a manifest
 * page). Drives the capture money path with a stable idempotency key reused on
 * retry (provider-replay-safe); never optimistic, never auto-resubmits.
 */
function PaymentRoute(): ReactNode {
  const [searchParams] = useSearchParams();
  const orderNo = searchParams.get('order') ?? '';
  const [idempotencyKey] = useState<string>(() => generateIdempotencyKey());

  const capture = useMutation<CheckoutCaptureResponse, ApiError, void>({
    mutationFn: () =>
      captureCheckout(
        { order_id: orderNo, provider_event_id: `evt_${orderNo}` },
        idempotencyKey,
      ),
    retry: false,
  });

  const status: PaymentStatus = capture.isPending
    ? 'processing'
    : capture.isSuccess
      ? 'success'
      : capture.error?.failureMode === 'payment_timeout'
        ? 'timeout'
        : capture.isError
          ? 'declined'
          : 'idle';

  return (
    <main className="stack">
      <PaymentPanel
        status={status}
        amountLabel={orderNo}
        onPay={() => capture.mutate()}
        onRetry={() => capture.mutate()}
      />
    </main>
  );
}
