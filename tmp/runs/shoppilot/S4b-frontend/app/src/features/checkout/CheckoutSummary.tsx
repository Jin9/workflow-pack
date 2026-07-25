import type { ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getCheckoutQuote } from '../../api/client';
import { ApiError } from '../../api/client';
import type { CheckoutQuote } from '../../api/types.gen';
import { formatMoney, moneyToPlain } from '../../lib/money';
import { failureModeToKey, useT } from '../../i18n/microcopy';
import styles from './CheckoutSummary.module.css';

/*
 * CheckoutSummary — Feature. Renders the SERVER-COMPUTED checkout quote
 * (subtotal / discount / shipping / total). The total is in an aria-live=polite
 * region so a recompute is announced (a11y-spec). Never computes a total locally
 * (state_ownership.computed_total = derived-from-server).
 */
export interface CheckoutSummaryProps {
  cartId: string;
  /** Lifts the server total up so the page can pass it to confirm display. */
  onQuoteLoaded?: (quote: CheckoutQuote) => void;
}

export function CheckoutSummary({ cartId }: CheckoutSummaryProps): ReactNode {
  const tr = useT();
  const query = useQuery<CheckoutQuote, ApiError>({
    queryKey: ['checkout-quote', cartId],
    queryFn: ({ signal }) => getCheckoutQuote(cartId, signal),
    retry: false,
  });

  if (query.isLoading) {
    return (
      <section className={styles.summary} aria-label={tr('screen.checkout.title')}>
        <div className="skeleton" />
        <div className="skeleton" />
      </section>
    );
  }

  if (query.isError) {
    return (
      <section className={styles.summary} aria-label={tr('screen.checkout.title')}>
        <p role="alert" className={styles.error}>
          {tr(failureModeToKey(query.error.failureMode))}
        </p>
      </section>
    );
  }

  if (!query.isSuccess) {
    return null;
  }

  const quote = query.data;
  return (
    <section className={styles.summary} aria-label={tr('screen.checkout.title')}>
      <Row label={tr('screen.checkout.title')} value={formatMoney(quote.subtotal)} muted />
      <Row label={tr('field.coupon.label')} value={`- ${formatMoney(quote.discount)}`} muted />
      <Row label="Shipping" value={formatMoney(quote.shipping)} muted />
      <div className={styles.total}>
        {/* Live region: recomputed server totals are announced politely. */}
        <span className={styles.totalLabel}>{tr('common.action.confirm')}</span>
        <output
          role="status"
          aria-live="polite"
          aria-label={`${moneyToPlain(quote.total)} ${quote.total.currency}`}
          className={styles.totalValue}
        >
          {formatMoney(quote.total)}
        </output>
      </div>
    </section>
  );
}

function Row({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}): ReactNode {
  return (
    <div className={styles.row}>
      <span className={muted === true ? 'muted' : undefined}>{label}</span>
      <span>{value}</span>
    </div>
  );
}
