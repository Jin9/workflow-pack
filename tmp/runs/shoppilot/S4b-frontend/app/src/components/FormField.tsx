import { forwardRef, useId, type InputHTMLAttributes } from 'react';
import styles from './FormField.module.css';

/*
 * FormField — Primitive. A labelled <input> with WCAG-AA error semantics:
 *   - programmatic <label htmlFor> association
 *   - aria-invalid on error
 *   - error text linked via aria-describedby AND rendered role="alert"
 *   - error is NOT conveyed by color alone (icon glyph + text)
 * No business logic, no app copy (caller passes label/error strings).
 */
export interface FormFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id' | 'aria-invalid'> {
  label: string;
  /** Resolved error message (already localized), or undefined when valid. */
  error?: string | undefined;
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(function FormField(
  { label, error, type, ...rest },
  ref,
) {
  const inputId = useId();
  const errorId = `${inputId}-error`;
  const hasError = error !== undefined && error.length > 0;

  return (
    <div className={styles.field}>
      <label className={styles.label} htmlFor={inputId}>
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        type={type ?? 'text'}
        className={hasError ? `${styles.input} ${styles.inputError}` : styles.input}
        aria-invalid={hasError}
        aria-describedby={hasError ? errorId : undefined}
        {...rest}
      />
      {hasError ? (
        <p id={errorId} className={styles.error} role="alert">
          {/* icon glyph carries meaning alongside the color, never color alone */}
          <span aria-hidden="true" className={styles.errorIcon}>
            ⚠
          </span>
          <span>{error}</span>
        </p>
      ) : null}
    </div>
  );
});
