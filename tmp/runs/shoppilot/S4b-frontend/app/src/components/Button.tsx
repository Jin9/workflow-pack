import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from 'react';
import styles from './Button.module.css';

/*
 * Button — Primitive. Pure presentation + a11y; no business logic, no copy.
 *   - native <button> => role=button + Enter/Space activation for free
 *   - visible focus ring (:focus-visible in global.css / module)
 *   - aria-busy + disabled while loading (blocks re-submit)
 *   - min 44x44 touch target (tokens)
 */
type Variant = 'primary' | 'secondary' | 'ghost';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  /** Loading => aria-busy=true, disabled, shows a busy label for SR. */
  loading?: boolean;
  /** SR-only text announced while loading (defaults to the visible children). */
  loadingLabel?: string;
  children: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = 'primary', loading = false, loadingLabel, disabled, children, type, ...rest },
  ref,
) {
  const isDisabled = disabled === true || loading;
  return (
    <button
      ref={ref}
      type={type ?? 'button'}
      className={`${styles.button} ${styles[variant]}`}
      aria-busy={loading}
      disabled={isDisabled}
      {...rest}
    >
      {loading ? (
        <>
          <span className={styles.spinner} aria-hidden="true" />
          <span className="visually-hidden">{loadingLabel ?? ''}</span>
          <span aria-hidden={loadingLabel !== undefined ? true : undefined}>{children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
});
