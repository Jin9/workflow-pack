import { type ReactElement, type ReactNode } from 'react';
import { render, type RenderResult } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nProvider, type Locale } from '../i18n/microcopy';

/*
 * Shared test renderer: wraps the UI in the same providers as main.tsx
 * (QueryClient + Router + I18n). Each call gets a fresh QueryClient so caches
 * never leak across tests.
 */
export interface RenderOptions {
  route?: string;
  locale?: Locale;
}

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: ReactElement,
  options: RenderOptions = {},
): RenderResult & { queryClient: QueryClient } {
  const queryClient = makeQueryClient();
  const locale: Locale = options.locale ?? 'th';
  const route = options.route ?? '/';

  function Wrapper({ children }: { children: ReactNode }): ReactElement {
    return (
      <QueryClientProvider client={queryClient}>
        <I18nProvider locale={locale}>
          <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
        </I18nProvider>
      </QueryClientProvider>
    );
  }

  const result = render(ui, { wrapper: Wrapper });
  return { ...result, queryClient };
}
