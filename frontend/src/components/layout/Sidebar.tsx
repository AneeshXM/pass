import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  Lock,
  Folder,
  Users,
  Shield,
  Activity,
  Settings,
} from 'lucide-react';
import clsx from 'clsx';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard className="w-5 h-5" /> },
  { label: 'All Vaults', path: '/vaults', icon: <Folder className="w-5 h-5" /> },
  { label: 'Passwords', path: '/credentials', icon: <Lock className="w-5 h-5" /> },
  { label: 'Activity', path: '/activity', icon: <Activity className="w-5 h-5" /> },
];

const adminItems: NavItem[] = [
  { label: 'Users', path: '/admin/users', icon: <Users className="w-5 h-5" />, adminOnly: true },
  { label: 'Groups', path: '/admin/groups', icon: <Users className="w-5 h-5" />, adminOnly: true },
  { label: 'Audit Logs', path: '/admin/audit', icon: <Shield className="w-5 h-5" />, adminOnly: true },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth();

  const isAdmin = user?.is_superuser || user?.role_id === 1;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-0 left-0 z-50 h-full w-64 bg-white dark:bg-dark-800 border-r border-gray-200 dark:border-dark-700 transition-transform duration-300 lg:translate-x-0 lg:top-16',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <nav className="flex flex-col h-full py-4">
          <div className="px-4 mb-4">
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Main Menu
            </h2>
          </div>

          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-4 py-3 mx-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                )
              }
              onClick={onClose}
            >
              <span className="mr-3">{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </NavLink>
          ))}

          {isAdmin && (
            <>
              <div className="px-4 mt-6 mb-4">
                <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Administration
                </h2>
              </div>

              {adminItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center px-4 py-3 mx-2 rounded-lg transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                    )
                  }
                  onClick={onClose}
                >
                  <span className="mr-3">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              ))}
            </>
          )}

          <div className="mt-auto px-4">
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-4 py-3 mx-2 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                )
              }
              onClick={onClose}
            >
              <span className="mr-3"><Settings className="w-5 h-5" /></span>
              <span className="font-medium">Settings</span>
            </NavLink>
          </div>
        </nav>
      </aside>
    </>
  );
}