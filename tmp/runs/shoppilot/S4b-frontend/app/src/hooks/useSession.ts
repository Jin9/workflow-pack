import { useMutation, useQuery, useQueryClient, type UseMutationResult } from '@tanstack/react-query';
import { login as loginApi, refresh as refreshApi } from '../api/client';
import { ApiError } from '../api/client';
import type { LoginRequest, SessionUser } from '../api/types.gen';
import { track } from '../analytics';

/*
 * useSession — Hook. SERVER-owned session (state_ownership.session = "server",
 * TanStack Query, cookie auth). The session identity lives ONLY in the query
 * cache + the httpOnly cookie — never in localStorage/sessionStorage.
 */
export const SESSION_QUERY_KEY = ['session'] as const;

export interface UseSessionResult {
  user: SessionUser | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  /** True only when refresh failed because the session expired. */
  isExpired: boolean;
  login: UseMutationResult<SessionUser, ApiError, LoginRequest>;
  logout: () => void;
}

export function useSession(): UseSessionResult {
  const queryClient = useQueryClient();

  const sessionQuery = useQuery<SessionUser | null, ApiError>({
    queryKey: SESSION_QUERY_KEY,
    queryFn: async ({ signal }) => {
      try {
        const res = await refreshApi(signal);
        return res.user;
      } catch (err) {
        // expired/invalid/replayed token => no session, not a hard error.
        if (err instanceof ApiError) return null;
        throw err;
      }
    },
    staleTime: 60_000,
    retry: false,
  });

  const loginMutation = useMutation<SessionUser, ApiError, LoginRequest>({
    mutationFn: async (body) => {
      track('login.submitted');
      const res = await loginApi(body);
      return res.user;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(SESSION_QUERY_KEY, user);
    },
  });

  const user = sessionQuery.data ?? undefined;

  return {
    user,
    isLoading: sessionQuery.isLoading,
    isAuthenticated: user !== undefined,
    isExpired:
      sessionQuery.data === null &&
      sessionQuery.fetchStatus === 'idle' &&
      sessionQuery.isFetched,
    login: loginMutation,
    logout: () => {
      queryClient.setQueryData(SESSION_QUERY_KEY, null);
    },
  };
}
