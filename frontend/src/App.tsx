import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import { Layout } from '@/components/layout';
import {
  LoginPage,
  RegisterPage,
  DashboardPage,
  VaultsPage,
  VaultDetailPage,
  SettingsPage,
} from '@/pages';
import { PageLoader } from '@/components/ui';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <PageLoader />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

// Public Route Component (redirects if authenticated)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <PageLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

// Placeholder pages for not-yet-implemented routes
function NotFoundPage() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-400">404</h1>
        <p className="text-xl text-gray-500 mt-2">Page not found</p>
      </div>
    </div>
  );
}

function CredentialsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">All Passwords</h1>
      <p className="text-gray-500 dark:text-gray-400">View all your credentials across all vaults.</p>
    </div>
  );
}

function ActivityPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Activity Log</h1>
      <p className="text-gray-500 dark:text-gray-400">View your recent account activity.</p>
    </div>
  );
}

function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">User Management</h1>
      <p className="text-gray-500 dark:text-gray-400">Manage system users and permissions.</p>
    </div>
  );
}

function AdminGroupsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Groups</h1>
      <p className="text-gray-500 dark:text-gray-400">Manage user groups and team collaboration.</p>
    </div>
  );
}

function AdminAuditPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Audit Logs</h1>
      <p className="text-gray-500 dark:text-gray-400">View system-wide audit logs.</p>
    </div>
  );
}

// App Routes Component
function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <div className="min-h-screen flex items-center justify-center">
              <p>Password reset functionality coming soon.</p>
            </div>
          </PublicRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="vaults" element={<VaultsPage />} />
        <Route path="vaults/:vaultId" element={<VaultDetailPage />} />
        <Route path="credentials" element={<CredentialsPage />} />
        <Route path="activity" element={<ActivityPage />} />
        <Route path="settings" element={<SettingsPage />} />
        
        {/* Admin Routes */}
        <Route path="admin/users" element={<AdminUsersPage />} />
        <Route path="admin/groups" element={<AdminGroupsPage />} />
        <Route path="admin/audit" element={<AdminAuditPage />} />
      </Route>

      {/* 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

// Main App Component
export function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AppRoutes />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#333',
                color: '#fff',
              },
              success: {
                style: {
                  background: '#10b981',
                },
              },
              error: {
                style: {
                  background: '#ef4444',
                },
              },
            }}
          />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;