import { useContext } from 'react';

import { AuthContext, type AuthContextValue } from '@/lib/auth-context';

export type { CurrentUser, Role } from '@/lib/auth-types';

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
