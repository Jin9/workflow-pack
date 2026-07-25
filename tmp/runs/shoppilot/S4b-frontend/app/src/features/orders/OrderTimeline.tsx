import type { ReactNode } from 'react';
import type { OrderStatus, OrderTimelineEntry } from '../../api/types.gen';
import { useT, type MicrocopyKey } from '../../i18n/microcopy';
import styles from './OrderTimeline.module.css';

/*
 * OrderTimeline — Feature. Renders an ordered status history as a semantic
 * <ol>/<li>. Status is conveyed by TEXT + ICON glyph (never color alone, a11y).
 */
export interface OrderTimelineProps {
  entries: OrderTimelineEntry[];
}

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

const STATUS_ICON: Readonly<Record<OrderStatus, string>> = {
  AWAITING_PAYMENT: '⏳',
  PAID: '✓',
  PAYMENT_FAILED: '✗',
  PAYMENT_TIMEOUT: '⏱',
  PACKING: '📦',
  SHIPPED: '🚚',
  DELIVERED: '🏠',
  CANCELLED: '⊘',
};

export function statusLabelKey(status: OrderStatus): MicrocopyKey {
  return STATUS_KEY[status];
}

export function OrderTimeline({ entries }: OrderTimelineProps): ReactNode {
  const tr = useT();
  return (
    <ol className={styles.timeline}>
      {entries.map((entry, index) => {
        const label = tr(STATUS_KEY[entry.status]);
        return (
          <li key={`${entry.status}-${index}`} className={styles.item}>
            <span aria-hidden="true" className={styles.icon}>
              {STATUS_ICON[entry.status]}
            </span>
            <span className={styles.label}>{label}</span>
            <time className={styles.time} dateTime={entry.at}>
              {formatTime(entry.at)}
            </time>
          </li>
        );
      })}
    </ol>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}
