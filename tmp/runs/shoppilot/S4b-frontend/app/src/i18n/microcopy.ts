import { createContext, createElement, useContext, type ReactNode } from 'react';
import data from './microcopy.json';

export type Locale = 'th' | 'en';

type StringEntry = { th: string; en: string };
type StringMap = Record<string, StringEntry>;

const STRINGS = data.strings as StringMap;

export type MicrocopyKey = keyof typeof data.strings;

const I18nContext = createContext<Locale>('th');

export function I18nProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: ReactNode;
}): ReactNode {
  return createElement(I18nContext.Provider, { value: locale }, children);
}

/**
 * Resolve a microcopy key for a locale. Falls back to the key itself if the key
 * is absent (defensive — keeps the UI rendering rather than crashing).
 */
export function t(key: MicrocopyKey, locale: Locale): string {
  const entry = STRINGS[key as string];
  if (entry === undefined) return key as string;
  return locale === 'th' ? entry.th : entry.en;
}

export function useLocale(): Locale {
  return useContext(I18nContext);
}

export function useT(): (key: MicrocopyKey) => string {
  const locale = useContext(I18nContext);
  return (key: MicrocopyKey) => t(key, locale);
}

/**
 * Map a contract failure_mode -> a microcopy key (S3 FE state-binding:
 * "error: failure_mode -> microcopy.json key"). Unknown modes fall back to a
 * neutral server error.
 */
export function failureModeToKey(failureMode: string): MicrocopyKey {
  switch (failureMode) {
    case 'coupon_expired':
      return 'field.coupon.error-expired';
    case 'out_of_stock':
    case 'insufficient_stock':
      return 'error.out-of-stock';
    case 'validation_error':
      return 'error.validation';
    case 'payment_declined':
    case 'amount_mismatch_rejected':
      return 'error.payment-declined';
    case 'payment_timeout':
      return 'error.payment-timeout';
    case 'invalid_credentials_generic':
    case 'rate_limited':
      return 'screen.login.error-state';
    case 'auth_required':
    case 'expired_token':
    case 'invalid_token':
    case 'replayed_token_family_revoked':
      return 'error.session-expired';
    case 'network_error':
      return 'error.network';
    default:
      return 'error.server';
  }
}
