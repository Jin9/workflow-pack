import { type ReactNode, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { getOrder } from '../api/client';
import { ApiError } from '../api/client';
import type { OrderDetail } from '../api/types.gen';
import { OrderTimeline, statusLabelKey } from '../features/orders/OrderTimeline';
import { formatMoney } from '../lib/money';
import { auditOnView, maskEmail, maskPhone } from '../lib/pii';
import { failureModeToKey, useT } from '../i18n/microcopy';
import { track } from '../analytics';
import styles from './OrderDetailPage.module.css';

/*
 * OrderDetailPage — Page. Server-owned order detail. Emits `order.viewed`.
 * PII: email/phone masked; shipping_address audit-on-view (never logged raw).
 * not_owner_denied / not_found => no order data disclosed.
 */
export function OrderDetailPage(): ReactNode {
  const tr = useT();
  const params = useParams<{ orderNo: string }>();
  const orderNo = params.orderNo ?? '';

  const query = useQuery<OrderDetail, ApiError>({
    queryKey: ['order', orderNo],
    queryFn: ({ signal }) => getOrder(orderNo, signal),
    enabled: orderNo.length > 0,
    retry: false,
  });

  useEffect(() => {
    if (query.data !== undefined) {
      track('order.viewed', { order_no: query.data.order_no });
    }
  }, [query.data]);

  return (
    <main className="stack" aria-labelledby="order-title">
      <div className="row">
        <h1 id="order-title" className="app-title">
          {tr('screen.order-detail.title')} {orderNo}
        </h1>
        <Link to="/orders" className={styles.back}>
          {tr('common.action.back')}
        </Link>
      </div>

      {query.isLoading ? <p role="status">{tr('common.status.loading')}</p> : null}

      {query.isError ? (
        <p role="alert" style={{ color: 'var(--color-semantic-error)' }}>
          {tr(failureModeToKey(query.error.failureMode))}
        </p>
      ) : null}

      {query.data !== undefined ? (
        <OrderDetailView order={query.data} />
      ) : null}
    </main>
  );
}

function OrderDetailView({ order }: { order: OrderDetail }): ReactNode {
  const tr = useT();
  return (
    <>
      <section className="card" aria-label={tr('screen.order-detail.title')}>
        <div className="row">
          <span className="muted">{tr('screen.order-detail.title')}</span>
          <strong>{tr(statusLabelKey(order.status))}</strong>
        </div>
        <div className="row">
          <span className="muted">{tr('common.action.confirm')}</span>
          <strong>{formatMoney(order.total)}</strong>
        </div>
        <div className="row">
          <span className="muted">{tr('field.email.label')}</span>
          {/* PII: masked */}
          <span>{maskEmail(order.customer_email)}</span>
        </div>
        <div className="row">
          <span className="muted">Phone</span>
          {/* PII: masked */}
          <span>{maskPhone(order.customer_phone)}</span>
        </div>
        <div className={styles.address}>
          <span className="muted">{tr('field.address.label')}</span>
          {/* PII: audit-on-view; raw value never logged */}
          <span>{auditOnView(order.order_no, order.shipping_address)}</span>
        </div>
        {order.tracking_no !== undefined ? (
          <div className="row">
            <span className="muted">{tr('common.action.track_order')}</span>
            <span>{order.tracking_no}</span>
          </div>
        ) : null}
      </section>

      <OrderTimeline entries={order.timeline} />
    </>
  );
}
