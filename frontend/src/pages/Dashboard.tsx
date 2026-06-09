import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { auditApi } from '@/services/api';
import { Card, CardHeader, CardBody, Spinner } from '@/components/ui';
import { useAuth } from '@/context/AuthContext';
import {
  Lock,
  Folder,
  Share2,
  Clock,
  Star,
  AlertTriangle,
  Plus,
  ArrowRight,
} from 'lucide-react';
import type { DashboardStats } from '@/types';

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await auditApi.getDashboard();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Welcome back, {user?.full_name || user?.email}!
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Here's an overview of your password vault
          </p>
        </div>
        <Link
          to="/vaults/new"
          className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Vault
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
              <Folder className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Vaults</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.total_vaults || 0}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-green-100 dark:bg-green-900/20 rounded-lg">
              <Lock className="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Passwords</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.total_credentials || 0}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-lg">
              <Share2 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Shared Vaults</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.shared_vaults || 0}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg">
              <Star className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Favorites</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.favorites_count || 0}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-red-100 dark:bg-red-900/20 rounded-lg">
              <Clock className="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Recent Activity</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.recent_activity || 0}
              </p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody className="flex items-center">
            <div className="p-3 bg-orange-100 dark:bg-orange-900/20 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">Expiring Soon</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {stats?.expiring_credentials || 0}
              </p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Quick Actions
            </h2>
          </CardHeader>
          <CardBody className="grid grid-cols-2 gap-4">
            <Link
              to="/credentials/new"
              className="flex items-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
            >
              <Plus className="w-5 h-5 text-primary-600 mr-3" />
              <span className="text-gray-900 dark:text-gray-100">Add Password</span>
            </Link>
            <Link
              to="/vaults"
              className="flex items-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
            >
              <Folder className="w-5 h-5 text-primary-600 mr-3" />
              <span className="text-gray-900 dark:text-gray-100">Browse Vaults</span>
            </Link>
            <Link
              to="/credentials"
              className="flex items-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
            >
              <Lock className="w-5 h-5 text-primary-600 mr-3" />
              <span className="text-gray-900 dark:text-gray-100">All Passwords</span>
            </Link>
            <Link
              to="/settings"
              className="flex items-center p-4 bg-gray-50 dark:bg-dark-700 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-600 transition-colors"
            >
              <Share2 className="w-5 h-5 text-primary-600 mr-3" />
              <span className="text-gray-900 dark:text-gray-100">Share Vault</span>
            </Link>
          </CardBody>
        </Card>

        {/* Security Tips */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Security Tips
            </h2>
          </CardHeader>
          <CardBody>
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="w-6 h-6 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Use unique passwords for each account
                </p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Enable two-factor authentication for extra security
                </p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Regularly update your passwords
                </p>
              </li>
              <li className="flex items-start">
                <div className="w-6 h-6 bg-yellow-100 dark:bg-yellow-900/20 rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-yellow-600 dark:text-yellow-400 text-sm">!</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Check for compromised passwords in settings
                </p>
              </li>
            </ul>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}