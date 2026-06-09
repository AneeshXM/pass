import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  LoginRequest,
  TokenResponse,
  User,
  UserCreate,
  UserUpdate,
  Vault,
  VaultCreate,
  VaultUpdate,
  Credential,
  CredentialCreate,
  CredentialUpdate,
  CredentialDetail,
  Tag,
  TagCreate,
  UserGroup,
  UserGroupCreate,
  Permission,
  AuditLog,
  DashboardStats,
  MFAStatus,
  MFASetupResponse,
  PaginatedResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let accessToken: string | null = localStorage.getItem('access_token');
let refreshToken: string | null = localStorage.getItem('refresh_token');

export const setTokens = (access: string, refresh: string) => {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const getAccessToken = () => accessToken;

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (refreshToken) {
        try {
          const response = await axios.post<TokenResponse>(
            `${API_BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          
          setTokens(response.data.access_token, response.data.refresh_token);
          
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          }
          
          return api(originalRequest);
        } catch {
          clearTokens();
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (data: LoginRequest) => {
    const response = await api.post<TokenResponse>('/auth/login', data);
    if (response.data.access_token) {
      setTokens(response.data.access_token, response.data.refresh_token);
    }
    return response.data;
  },

  verifyMFA: async (code: string) => {
    const response = await api.post<TokenResponse>('/auth/verify-mfa', null, {
      params: { code },
    });
    setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  },

  refresh: async (refresh: string) => {
    const response = await api.post<TokenResponse>('/auth/refresh', {
      refresh_token: refresh,
    });
    setTokens(response.data.access_token, response.data.refresh_token);
    return response.data;
  },

  logout: async () => {
    await api.post('/auth/logout');
    clearTokens();
  },

  getMe: async () => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  resetPassword: async (email: string) => {
    await api.post('/auth/password-reset', { email });
  },
};

// Users API
export const usersApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const response = await api.get<PaginatedResponse<User>>('/users/', { params });
    return response.data;
  },

  create: async (data: UserCreate) => {
    const response = await api.post<User>('/users/', data);
    return response.data;
  },

  getMe: async () => {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  updateMe: async (data: UserUpdate) => {
    const response = await api.put<User>('/users/me', data);
    return response.data;
  },

  changePassword: async (current: string, newPassword: string) => {
    await api.put('/users/me/password', {
      current_password: current,
      new_password: newPassword,
    });
  },

  get: async (id: number) => {
    const response = await api.get<User>(`/users/${id}`);
    return response.data;
  },

  update: async (id: number, data: UserUpdate) => {
    const response = await api.put<User>(`/users/${id}`, data);
    return response.data;
  },

  updateRole: async (id: number, roleId: number) => {
    await api.put(`/users/${id}/role`, null, { params: { role_id: roleId } });
  },

  activate: async (id: number) => {
    await api.post(`/users/${id}/activate`);
  },

  deactivate: async (id: number) => {
    await api.post(`/users/${id}/deactivate`);
  },

  listRoles: async () => {
    const response = await api.get<User[]>('/users/roles/');
    return response.data;
  },
};

// Vaults API
export const vaultsApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string; shared_only?: boolean }) => {
    const response = await api.get<PaginatedResponse<Vault>>('/vaults/', { params });
    return response.data;
  },

  create: async (data: VaultCreate) => {
    const response = await api.post<Vault>('/vaults/', data);
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Vault>(`/vaults/${id}`);
    return response.data;
  },

  update: async (id: number, data: VaultUpdate) => {
    const response = await api.put<Vault>(`/vaults/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await api.delete(`/vaults/${id}`);
  },

  share: async (vaultId: number, userId: number, permissions?: Partial<Permission>) => {
    await api.post(`/vaults/${vaultId}/share`, null, {
      params: {
        user_id: userId,
        can_read: permissions?.can_read ?? true,
        can_write: permissions?.can_write ?? false,
        can_share: permissions?.can_share ?? false,
        can_delete: permissions?.can_delete ?? false,
      },
    });
  },

  unshare: async (vaultId: number, userId: number) => {
    await api.delete(`/vaults/${vaultId}/share/${userId}`);
  },

  getPermissions: async (vaultId: number) => {
    const response = await api.get<Permission[]>(`/vaults/${vaultId}/permissions`);
    return response.data;
  },
};

// Credentials API
export const credentialsApi = {
  list: async (vaultId: number, params?: { skip?: number; limit?: number; search?: string; favorites_only?: boolean }) => {
    const response = await api.get<PaginatedResponse<Credential>>('/credentials/', {
      params: { vault_id: vaultId, ...params },
    });
    return response.data;
  },

  listAll: async (params?: { skip?: number; limit?: number; search?: string }) => {
    const response = await api.get<PaginatedResponse<Credential>>('/credentials/all/', { params });
    return response.data;
  },

  create: async (data: CredentialCreate) => {
    const response = await api.post<Credential>('/credentials/', data);
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<Credential>(`/credentials/${id}`);
    return response.data;
  },

  getWithPassword: async (id: number) => {
    const response = await api.get<CredentialDetail>(`/credentials/${id}/password`);
    return response.data;
  },

  update: async (id: number, data: CredentialUpdate) => {
    const response = await api.put<Credential>(`/credentials/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await api.delete(`/credentials/${id}`);
  },

  toggleFavorite: async (id: number) => {
    const response = await api.post<{ favorite: boolean }>(`/credentials/${id}/favorite`);
    return response.data;
  },
};

// Tags API
export const tagsApi = {
  list: async (vaultId: number) => {
    const response = await api.get<Tag[]>(`/tags/`, { params: { vault_id: vaultId } });
    return response.data;
  },

  create: async (data: TagCreate) => {
    const response = await api.post<Tag>('/tags/', data);
    return response.data;
  },

  delete: async (id: number) => {
    await api.delete(`/tags/${id}`);
  },
};

// Groups API
export const groupsApi = {
  list: async () => {
    const response = await api.get<UserGroup[]>('/groups/');
    return response.data;
  },

  create: async (data: UserGroupCreate) => {
    const response = await api.post<UserGroup>('/groups/', data);
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get<UserGroup>(`/groups/${id}`);
    return response.data;
  },

  update: async (id: number, data: UserGroupCreate) => {
    const response = await api.put<UserGroup>(`/groups/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    await api.delete(`/groups/${id}`);
  },

  addMembers: async (groupId: number, userIds: number[]) => {
    await api.post(`/groups/${groupId}/members`, { user_ids: userIds });
  },

  removeMember: async (groupId: number, userId: number) => {
    await api.delete(`/groups/${groupId}/members`, { params: { user_id: userId } });
  },
};

// Audit API
export const auditApi = {
  list: async (params?: { skip?: number; limit?: number; user_id?: number; action?: string }) => {
    const response = await api.get<PaginatedResponse<AuditLog>>('/audit/logs', { params });
    return response.data;
  },

  listMy: async (params?: { skip?: number; limit?: number; action?: string }) => {
    const response = await api.get<PaginatedResponse<AuditLog>>('/audit/logs/me', { params });
    return response.data;
  },

  getDashboard: async () => {
    const response = await api.get<DashboardStats>('/audit/dashboard');
    return response.data;
  },
};

// MFA API
export const mfaApi = {
  getStatus: async () => {
    const response = await api.get<MFAStatus>('/mfa/status');
    return response.data;
  },

  setup: async () => {
    const response = await api.post<MFASetupResponse>('/mfa/setup');
    return response.data;
  },

  enable: async (password: string, code: string) => {
    await api.post('/mfa/enable', { password, code });
  },

  disable: async (password: string, code: string) => {
    await api.post('/mfa/disable', { password, code });
  },

  verify: async (code: string) => {
    const response = await api.post<{ valid: boolean; is_backup: boolean }>('/mfa/verify', { code });
    return response.data;
  },

  regenerateBackupCodes: async (password: string) => {
    const response = await api.post<{ backup_codes: string[] }>('/mfa/regenerate-backup-codes', null, {
      params: { password },
    });
    return response.data;
  },
};

export default api;