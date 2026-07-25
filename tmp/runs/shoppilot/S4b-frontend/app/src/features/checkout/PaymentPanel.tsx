import type { ReactNode } from 'react';
import { Button } from '../../components/Button';
import { useT } from '../../i18n/microcopy';
import { track } from '../../analytics';
import styles from './PaymentPanel.module.css';

/*
 * PaymentPanel — Feature. Triggers the mock provider and renders idle /
 * processing / declined / timeout. No PAN/CVV (PSP-hosted, PCI scope-excluded).
 * Money path => never optimistic. Declined surfaces a role="alert" + a
 * keyboard-reachable <button> retry that reuses the SAME idempotency key.
 */
export type PaymentStatus = 'idle' | 'processing' | 'declined' | 'timeout' | 'success';

export interface PaymentPanelProps {
  status: PaymentStatus;
  amountLabel: string;
  onPay: () => void;
  onRetry: () => void;
}

export function PaymentPanel({
  status,
  amountLabel,
  onPay,
  onRetry,
}: PaymentPanelProps): ReactNode {
  const tr = useT();
  const isProcessing = status === 'processing';
  const isFailed = status === 'declined' || status === 'timeout';

  return (
    <section className={styles.panel} aria-label={tr('screen.payment.title')}>
      <div className={styles.amount}>
        <span className="muted">{tr('screen.payment.title')}</span>
        <strong className={styles.amountValue}>{amountLabel}</strong>
      </div>

      {isProcessing ? (
        <p role="status" aria-live="polite" className={styles.processing}>
          {tr('screen.payment.processing-state')}
        </p>
      ) : null}

      {status === 'success' ? (
        <p role="status" aria-live="polite" className={styles.success}>
          {tr('common.status.success')}
        </p>
      ) : null}

      {isFailed ? (
        <div className={styles.declined} role="alert">
          <span aria-hidden="true" className={styles.declinedIcon}>
            ⚠
          </span>
          <span>
            {status === 'timeout'
              ? tr('error.payment-timeout')
              : tr('error.payment-declined')}
          </span>
        </div>
      ) : null}

      {isFailed ? (
        <Button
          variant="primary"
          onClick={() => {
            track('payment.submitted');
            onRetry();
          }}
        >
          {tr('common.action.retry')}
        </Button>
      ) : (
        <Button
          variant="primary"
          loading={isProcessing}
          loadingLabel={tr('screen.payment.processing-state')}
          disabled={status === 'success'}
          onClick={() => {
            track('payment.submitted');
            onPay();
          }}
        >
          {tr('common.action.pay')}
        </Button>
      )}
    </section>
  );
}
