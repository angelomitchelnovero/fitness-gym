export type Role = 'admin' | 'customer';

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  role: Role;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}
