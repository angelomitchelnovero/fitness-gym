import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

import { api, getToken, setToken, toApiError } from '@/lib/api';
import { AuthContext, type AuthContextValue, type AuthState } from '@/lib/auth-context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, loading: true, error: null });

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setState({ user: null, loading: false, error: null });
      return;
    }
    try {
      const res = await api.get('/auth/me');
      setState({ user: res.data, loading: false, error: null });
    } catch (err) {
      setToken(null);
      setState({ user: null, loading: false, error: toApiError(err).message });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await api.post<{ access_token: string }>('/auth/login', { email, password });
      setToken(res.data.access_token);
      const userRes = await api.get('/auth/me');
      const user = userRes.data;
      setState({ user, loading: false, error: null });
      return user;
    },
    [],
  );

  const register = useCallback<AuthContextValue['register']>(
    async (input) => {
      const res = await api.post<{ access_token: string }>('/auth/register', input);
      setToken(res.data.access_token);
      await refresh();
    },
    [refresh],
  );

  const logout = useCallback(() => {
    setToken(null);
    setState({ user: null, loading: false, error: null });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ ...state, login, register, logout, refresh }),
    [state, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
