import { useCallback, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ApiError, confirmCheckout } from '../api/client';
import type { CheckoutConfirmRequest, ConfirmedOrder } from '../api/types.gen';
import { track } from '../analytics';

/*
 * useIdempotentConfirm — Hook. Owns the idempotency-key lifecycle for the
 * checkout-confirm MONEY path.
 *
 * Banking-grade rules enforced here:
 *  - One UUIDv4 idempotency_key per confirm attempt-sequence; generated once.
 *  - On a network error after submit, the SAME key is reused on retry
 *    (compensating action: "surface retry with the same idempotency_key").
 *  - NEVER auto-resubmits — retry only fires when the user calls retry().
 *  - submit is disabled in-flight (isSubmitting) to block double-fire.
 *  - This path is NEVER optimistic.
 */

/** RFC-4122 v4 UUID. Uses crypto.randomUUID when available; deterministic shape. */
export function generateIdempotencyKey(): string {
  const c: Crypto | undefined =
    typeof globalThis.crypto !== 'undefined' ? globalThis.crypto : undefined;
  if (c !== undefined && typeof c.randomUUID === 'function') {
    return c.randomUUID();
  }
  // Fallback: build a v4 from getRandomValues (still cryptographically random).
  const bytes = new Uint8Array(16);
  if (c !== undefined && typeof c.getRandomValues === 'function') {
    c.getRandomValues(bytes);
  } else {
    for (let i = 0; i < 16; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  }
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40;
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80;
  const hex: string[] = [];
  for (let i = 0; i < 16; i += 1) hex.push((bytes[i] ?? 0).toString(16).padStart(2, '0'));
  return (
    `${hex[0]}${hex[1]}${hex[2]}${hex[3]}-${hex[4]}${hex[5]}-` +
    `${hex[6]}${hex[7]}-${hex[8]}${hex[9]}-${hex[10]}${hex[11]}${hex[12]}${hex[13]}${hex[14]}${hex[15]}`
  );
}

export interface ConfirmInput {
  cart_id: string;
  address: string;
  coupon?: string | undefined;
}

export interface UseIdempotentConfirmResult {
  /** Submit the confirm. No-op while a request is in flight. */
  submit: (input: ConfirmInput) => void;
  /** Retry the last failed submit with the SAME idempotency key. */
  retry: () => void;
  /** Stable per attempt-sequence; identical across retries until success/reset. */
  idempotencyKey: string;
  isSubmitting: boolean;
  isSuccess: boolean;
  order: ConfirmedOrder | undefined;
  error: ApiError | undefined;
  reset: () => void;
}

export function useIdempotentConfirm(): UseIdempotentConfirmResult {
  // Generated once; reused across retries until an explicit reset().
  const keyRef = useRef<string>(generateIdempotencyKey());
  const lastInputRef = useRef<ConfirmInput | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState<string>(keyRef.current);

  const mutation = useMutation<ConfirmedOrder, ApiError, CheckoutConfirmRequest>({
    mutationFn: async (body) => {
      const res = await confirmCheckout(body);
      return res.order;
    },
    // No retry: a network error must surface a manual retry, never auto-resubmit.
    retry: false,
  });

  const fire = useCallback(
    (input: ConfirmInput) => {
      if (mutation.isPending) return; // disabled in-flight; no double fire.
      const body: CheckoutConfirmRequest = {
        cart_id: input.cart_id,
        address: input.address,
        idempotency_key: keyRef.current,
        ...(input.coupon !== undefined ? { coupon: input.coupon } : {}),
      };
      mutation.mutate(body);
    },
    [mutation],
  );

  const submit = useCallback(
    (input: ConfirmInput) => {
      track('checkout.confirm.clicked');
      lastInputRef.current = input;
      fire(input);
    },
    [fire],
  );

  const retry = useCallback(() => {
    const last = lastInputRef.current;
    if (last === null) return;
    // Same key on purpose — provider/server replay-collapses the duplicate.
    fire(last);
  }, [fire]);

  const reset = useCallback(() => {
    const next = generateIdempotencyKey();
    keyRef.current = next;
    setIdempotencyKey(next);
    lastInputRef.current = null;
    mutation.reset();
  }, [mutation]);

  return {
    submit,
    retry,
    idempotencyKey,
    isSubmitting: mutation.isPending,
    isSuccess: mutation.isSuccess,
    order: mutation.data,
    error: mutation.error ?? undefined,
    reset,
  };
}
