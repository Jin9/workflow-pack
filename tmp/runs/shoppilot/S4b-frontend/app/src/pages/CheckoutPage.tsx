import { type ReactNode, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { CheckoutSummary } from '../features/checkout/CheckoutSummary';
import { FormField } from '../components/FormField';
import { Button } from '../components/Button';
import { useIdempotentConfirm } from '../hooks/useIdempotentConfirm';
import { useCartStore } from '../store/cart';
import { failureModeToKey, useT } from '../i18n/microcopy';

/*
 * CheckoutPage — Page. Owns the checkout boundary:
 *   - CheckoutSummary (server-computed total, live region)
 *   - address (required) + coupon (optional) form  [checkout_form = RHF + Zod]
 *   - confirm via useIdempotentConfirm (money path; never optimistic; retry
 *     reuses the SAME idempotency key, never auto-resubmits)
 * Cart is client-owned (Zustand); total is derived-from-server (never local).
 */
const schema = z.object({
  address: z.string().min(1, 'required'),
  coupon: z.string().optional(),
});

type CheckoutForm = z.infer<typeof schema>;

export function CheckoutPage(): ReactNode {
  const tr = useT();
  const navigate = useNavigate();
  const cartId = useCartStore((s) => s.cartId);
  const confirm = useIdempotentConfirm();

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<CheckoutForm>({
    resolver: zodResolver(schema),
    defaultValues: { address: '', coupon: '' },
  });

  const onSubmit = handleSubmit((values) => {
    confirm.submit({
      cart_id: cartId,
      address: values.address,
      ...(values.coupon !== undefined && values.coupon.length > 0
        ? { coupon: values.coupon }
        : {}),
    });
  });

  // Success => proceed to payment for the created (awaiting-payment) order.
  // Effect (not render body) so navigation fires exactly once on success.
  const confirmedOrderNo = confirm.isSuccess ? confirm.order?.order_no : undefined;
  useEffect(() => {
    if (confirmedOrderNo !== undefined) {
      navigate(`/checkout/payment?order=${confirmedOrderNo}`);
    }
  }, [confirmedOrderNo, navigate]);

  const error = confirm.error;
  // Coupon-expired is a non-blocking, neutral error (re-checked server-side).
  const isCouponError = error?.failureMode === 'coupon_expired';

  function retrySameKey(): void {
    confirm.retry();
  }

  return (
    <main className="stack" aria-labelledby="checkout-title">
      <h1 id="checkout-title" className="app-title">
        {tr('screen.checkout.title')}
      </h1>

      <CheckoutSummary cartId={cartId} />

      <form className="stack" onSubmit={onSubmit} noValidate>
        <FormField
          label={tr('field.address.label')}
          autoComplete="shipping street-address"
          error={errors.address !== undefined ? tr('error.validation') : undefined}
          {...register('address')}
        />
        <FormField label={tr('field.coupon.label')} {...register('coupon')} />

        {error !== undefined ? (
          <p role="alert" style={{ color: 'var(--color-semantic-error)', margin: 0 }}>
            {tr(failureModeToKey(error.failureMode))}
          </p>
        ) : null}

        {/* On a network error after submit: surface a manual retry that reuses
            the same idempotency key. Never auto-resubmits. */}
        {error?.failureMode === 'network_error' ? (
          <Button type="button" variant="secondary" onClick={retrySameKey}>
            {tr('common.action.retry')}
          </Button>
        ) : null}

        <Button
          type="submit"
          variant="primary"
          loading={confirm.isSubmitting}
          loadingLabel={tr('common.status.loading')}
          disabled={confirm.isSubmitting}
        >
          {tr('common.action.confirm')}
        </Button>

        {isCouponError ? (
          <p className="muted" style={{ margin: 0 }}>
            {/* coupon-expired does not block; the address remains submittable */}
            {tr('field.coupon.label')}: {getValues('coupon')}
          </p>
        ) : null}
      </form>
    </main>
  );
}
