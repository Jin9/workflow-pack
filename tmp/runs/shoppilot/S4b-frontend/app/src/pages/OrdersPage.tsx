import { type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listOrders } from '../api/client';
import { ApiError } from '../api/client';
import type { OrderListResponse, OrderStatus } from '../api/types.gen';
import { formatMoney } from '../lib/money';
import { failureModeToKey, useT, type MicrocopyKey } from '../i18n/microcopy';
import styles from './OrdersPage.module.css';

/*
 * OrdersPage — Page. Server-owned order_list (TanStack Query). Own-data-only
 * (the cookie session scopes the list server-side). Status by text + icon.
 */
const STATUS_KEY: Readonly<Record<OrderStatus, MicrocopyKey>> = {
  AWAITING_PAYMENT: 'order.status.AWAITING_PAYMENT',
  PAID: 'order.status.PAID',
  PAYMENT_FAILED: 'order.status.PAYMENT_FAILED',
  PAYMENT_TIMEOUT: 'order.status.PAYMENT_TIMEOUT',
  PACKING: 'order.status.PACKING',
  SHIPPED: 'order.status.SHIPPED',
  DELIVERED: 'order.status.DELIVERED',
  CANCELLED: 'order.status.CANCELLED',
};

export function OrdersPage(): ReactNode {
  const tr = useT();
  const query = useQuery<OrderListResponse, ApiError>({
    queryKey: ['orders'],
    queryFn: ({ signal }) => listOrders(signal),
    retry: false,
  });

  return (
    <main className="stack" aria-labelledby="orders-title">
      <h1 id="orders-title" className="app-title">
        {tr('screen.orders.title')}
      </h1>

      {query.isLoading ? (
        <p role="status">{tr('common.status.loading')}</p>
      ) : null}

      {query.isError ? (
        <p role="alert" style={{ color: 'var(--color-semantic-error)' }}>
          {tr(failureModeToKey(query.error.failureMode))}
        </p>
      ) : null}

      {query.data !== undefined && query.data.orders.length === 0 ? (
        <p className="muted">{tr('screen.orders.empty-state')}</p>
      ) : null}

      {query.data !== undefined && query.data.orders.length > 0 ? (
        <ul className={styles.list}>
          {query.data.orders.map((order) => (
            <li key={order.order_no} className="card">
              <div className="row">
                <span className={styles.orderNo}>{order.order_no}</span>
                <span className={styles.badge}>{tr(STATUS_KEY[order.status])}</span>
              </div>
              <div className="row">
                <span>{formatMoney(order.total)}</span>
                <Link to={`/orders/${order.order_no}`} className={styles.track}>
                  {tr('common.action.track_order')}
                </Link>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </main>
  );
}
