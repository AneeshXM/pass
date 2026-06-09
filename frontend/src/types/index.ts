// User types
export interface User {
  id: number;
  email: string;
  username?: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  role_id: number;
  mfa_enabled: boolean;
  avatar_url?: string;
  phone?: string;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions?: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserCreate {
  email: string;
  username?: string;
  full_name?: string;
  password: string;
}

export interface UserUpdate {
  email?: string;
  username?: string;
  full_name?: string;
  phone?: string;
  avatar_url?: string;
}

// Vault types
export interface Vault {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_shared: boolean;
  owner_id: number;
  group_id?: number;
  created_at: string;
  updated_at: string;
}

export interface VaultCreate {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_shared?: boolean;
  group_id?: number;
}

export interface VaultUpdate {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
  is_shared?: boolean;
  group_id?: number;
}

// Credential types
export interface Credential {
  id: number;
  name: string;
  url?: string;
  username?: string;
  notes?: string;
  favorite: boolean;
  vault_id: number;
  user_id: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
  tags?: Tag[];
}

export interface CredentialCreate {
  name: string;
  url?: string;
  username?: string;
  password: string;
  notes?: string;
  vault_id: number;
  expires_at?: string;
  tag_ids?: number[];
}

export interface CredentialUpdate {
  name?: string;
  url?: string;
  username?: string;
  password?: string;
  notes?: string;
  favorite?: boolean;
  expires_at?: string;
  tag_ids?: number[];
}

export interface CredentialDetail extends Credential {
  password: string;
}

// Tag types
export interface Tag {
  id: number;
  name: string;
  color?: string;
  vault_id?: number;
  created_at: string;
}

export interface TagCreate {
  name: string;
  color?: string;
  vault_id?: number;
}

// User Group types
export interface UserGroup {
  id: number;
  name: string;
  description?: string;
  created_by: number;
  created_at: string;
  member_count?: number;
}

export interface UserGroupCreate {
  name: string;
  description?: string;
}

// Permission types
export interface Permission {
  id: number;
  user_id: number;
  vault_id: number;
  can_read: boolean;
  can_write: boolean;
  can_share: boolean;
  can_delete: boolean;
  created_at: string;
}

// Audit types
export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  details?: string;
  ip_address?: string;
  user_agent?: string;
  status: string;
  created_at: string;
}

// Dashboard types
export interface DashboardStats {
  total_vaults: number;
  total_credentials: number;
  shared_vaults: number;
  expiring_credentials: number;
  recent_activity: number;
  favorites_count: number;
}

// MFA types
export interface MFAStatus {
  enabled: boolean;
  has_recovery_codes: boolean;
}

export interface MFASetupResponse {
  secret: string;
  qr_code: string;
  backup_codes: string[];
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// Context types
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (data: UserCreate) => Promise<void>;
}