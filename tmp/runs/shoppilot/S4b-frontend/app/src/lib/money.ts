import type { Money } from '../api/types.gen';

/*
 * money.ts — FORMATTING ONLY.
 *
 * Banking-grade rule (state_ownership.computed_total = "derived" from the SERVER):
 * this module NEVER computes, sums, or optimistically updates a total. It takes a
 * server-computed Money value and renders it. There is intentionally no `add`,
 * `subtotal`, or `applyCoupon` here.
 */

const SYMBOL: Readonly<Record<Money['currency'], string>> = {
  THB: '฿',
};

/**
 * Format a server-computed Money value for display. Pure: minor units -> string.
 * No rounding decisions, no arithmetic across line items.
 */
export function formatMoney(value: Money): string {
  const major = value.amount_minor / 100;
  const formatted = major.toLocaleString('th-TH', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const symbol = SYMBOL[value.currency];
  return `${symbol}${formatted}`;
}

/** Plain numeric (major units) for an aria-label / SR-only string. */
export function moneyToPlain(value: Money): string {
  return (value.amount_minor / 100).toFixed(2);
}
