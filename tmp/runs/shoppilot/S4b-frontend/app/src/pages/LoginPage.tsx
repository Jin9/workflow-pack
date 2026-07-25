import { type ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate } from 'react-router-dom';
import { FormField } from '../components/FormField';
import { Button } from '../components/Button';
import { useSession } from '../hooks/useSession';
import { failureModeToKey, useT } from '../i18n/microcopy';

/*
 * LoginPage — Page. Owns the login form boundary. Session is server-owned
 * (useSession / cookie). Generic auth error (no account enumeration).
 * checkout_form-style validation is presence-only client side (password rules
 * are server-side; no client regex on the password — leaks policy).
 */
const schema = z.object({
  email: z.string().min(1, 'required'),
  password: z.string().min(1, 'required'),
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage(): ReactNode {
  const tr = useT();
  const navigate = useNavigate();
  const session = useSession();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = handleSubmit((values) => {
    session.login.mutate(values, {
      onSuccess: () => {
        navigate('/orders');
      },
    });
  });

  const authError = session.login.error;

  return (
    <main className="stack" aria-labelledby="login-title">
      <h1 id="login-title" className="app-title">
        {tr('screen.login.title')}
      </h1>

      {authError !== null && authError !== undefined ? (
        <p role="alert" style={{ color: 'var(--color-semantic-error)', margin: 0 }}>
          {tr(failureModeToKey(authError.failureMode))}
        </p>
      ) : null}

      <form className="stack" onSubmit={onSubmit} noValidate>
        <FormField
          label={tr('field.email.label')}
          type="email"
          autoComplete="email"
          placeholder={tr('field.email.placeholder')}
          error={errors.email !== undefined ? tr('field.email.error-required') : undefined}
          {...register('email')}
        />
        <FormField
          label={tr('field.password.label')}
          type="password"
          autoComplete="current-password"
          error={
            errors.password !== undefined ? tr('field.password.error-required') : undefined
          }
          {...register('password')}
        />
        <Button
          type="submit"
          variant="primary"
          loading={session.login.isPending}
          loadingLabel={tr('common.status.loading')}
        >
          {tr('common.action.login')}
        </Button>
      </form>
    </main>
  );
}
