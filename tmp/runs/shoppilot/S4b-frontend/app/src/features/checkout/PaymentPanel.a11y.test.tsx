import { describe, expect, it, vi } from 'vitest';
import { axe } from 'jest-axe';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '../../test/render';
import { PaymentPanel } from './PaymentPanel';

describe('PaymentPanel a11y', () => {
  it('has no axe violations in the idle state', async () => {
    const { container } = renderWithProviders(
      <PaymentPanel status="idle" amountLabel="฿440.00" onPay={() => {}} onRetry={() => {}} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations in the declined state', async () => {
    const { container } = renderWithProviders(
      <PaymentPanel
        status="declined"
        amountLabel="฿440.00"
        onPay={() => {}}
        onRetry={() => {}}
      />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('exposes the declined message as role="alert"', () => {
    renderWithProviders(
      <PaymentPanel
        status="declined"
        amountLabel="฿440.00"
        onPay={() => {}}
        onRetry={() => {}}
      />,
    );
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent(/ดำเนินการชำระเงิน|completed/i);
  });

  it('renders retry as a keyboard-reachable native button', () => {
    renderWithProviders(
      <PaymentPanel
        status="declined"
        amountLabel="฿440.00"
        onPay={() => {}}
        onRetry={() => {}}
      />,
    );
    const retry = screen.getByRole('button', { name: /ลองอีกครั้ง|try again/i });
    expect(retry.tagName).toBe('BUTTON');
    // Native buttons are in the tab order (no negative tabindex).
    expect(retry).not.toHaveAttribute('tabindex', '-1');
  });

  it('announces the timeout failure (distinct copy) with role="alert" and a retry', () => {
    renderWithProviders(
      <PaymentPanel status="timeout" amountLabel="฿440.00" onPay={() => {}} onRetry={() => {}} />,
    );
    expect(screen.getByRole('alert')).toHaveTextContent(/หมดเวลา|timed out/i);
    expect(screen.getByRole('button', { name: /ลองอีกครั้ง|try again/i })).toBeInTheDocument();
  });

  it('shows a polite processing status and a busy Pay button while processing', () => {
    renderWithProviders(
      <PaymentPanel status="processing" amountLabel="฿440.00" onPay={() => {}} onRetry={() => {}} />,
    );
    const status = screen.getByRole('status');
    expect(status).toHaveTextContent(/ดำเนินการ|processing/i);
    expect(screen.getByRole('button', { name: /ชำระเงิน|pay/i })).toHaveAttribute('aria-busy', 'true');
  });

  it('shows a polite success status and disables Pay on success', () => {
    renderWithProviders(
      <PaymentPanel status="success" amountLabel="฿440.00" onPay={() => {}} onRetry={() => {}} />,
    );
    expect(screen.getByRole('status')).toHaveTextContent(/สำเร็จ|done/i);
    expect(screen.getByRole('button', { name: /ชำระเงิน|pay/i })).toBeDisabled();
  });

  it('fires onPay when idle and onRetry when failed (analytics-tracked actions)', async () => {
    const user = userEvent.setup();
    const onPay = vi.fn();
    const onRetry = vi.fn();

    const { rerender } = renderWithProviders(
      <PaymentPanel status="idle" amountLabel="฿440.00" onPay={onPay} onRetry={onRetry} />,
    );
    await user.click(screen.getByRole('button', { name: /ชำระเงิน|pay/i }));
    expect(onPay).toHaveBeenCalledTimes(1);

    rerender(
      <PaymentPanel status="declined" amountLabel="฿440.00" onPay={onPay} onRetry={onRetry} />,
    );
    await user.click(screen.getByRole('button', { name: /ลองอีกครั้ง|try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
