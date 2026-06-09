import React, { useState } from 'react';
import { usersApi, mfaApi } from '@/services/api';
import { Card, CardHeader, CardBody, Button, Input } from '@/components/ui';
import { useAuth } from '@/context/AuthContext';
import { User, Lock, Shield, Smartphone, Download } from 'lucide-react';
import toast from 'react-hot-toast';

export function SettingsPage() {
  const { user, checkAuth } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'mfa' | 'backup'>('profile');

  // Profile state
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    avatar_url: user?.avatar_url || '',
  });
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);

  // Password state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false);

  // MFA state
  const [mfaSetupData, setMfaSetupData] = useState<{ secret: string; qr_code: string; backup_codes: string[] } | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaPassword, setMfaPassword] = useState('');

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdatingProfile(true);
    try {
      await usersApi.updateMe(profileData);
      toast.success('Profile updated successfully');
      checkAuth();
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setIsUpdatingPassword(true);
    try {
      await usersApi.changePassword(passwordData.current_password, passwordData.new_password);
      toast.success('Password changed successfully');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (error) {
      toast.error('Failed to change password');
    } finally {
      setIsUpdatingPassword(false);
    }
  };

  const handleSetupMFA = async () => {
    try {
      const data = await mfaApi.setup();
      setMfaSetupData(data);
    } catch (error) {
      toast.error('Failed to setup MFA');
    }
  };

  const handleEnableMFA = async () => {
    if (!mfaSetupData || !mfaPassword || !mfaCode) return;

    try {
      await mfaApi.enable(mfaPassword, mfaCode);
      toast.success('MFA enabled successfully! Save your backup codes.');
      setMfaSetupData(null);
      setMfaCode('');
      setMfaPassword('');
      checkAuth();
    } catch (error) {
      toast.error('Failed to enable MFA. Please check your code and password.');
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: <User className="w-4 h-4" /> },
    { id: 'security', label: 'Security', icon: <Lock className="w-4 h-4" /> },
    { id: 'mfa', label: 'Two-Factor', icon: <Smartphone className="w-4 h-4" /> },
    { id: 'backup', label: 'Backup', icon: <Download className="w-4 h-4" /> },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Settings
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Tabs */}
        <div className="lg:w-64">
          <Card>
            <CardBody className="p-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full flex items-center px-4 py-3 rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700'
                  }`}
                >
                  <span className="mr-3">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </CardBody>
          </Card>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Profile Information</h2>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleUpdateProfile} className="space-y-4">
                  <Input
                    label="Email"
                    value={user?.email || ''}
                    disabled
                  />
                  <Input
                    label="Full Name"
                    value={profileData.full_name}
                    onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                  />
                  <Input
                    label="Phone"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                  />
                  <Button type="submit" isLoading={isUpdatingProfile}>
                    Save Changes
                  </Button>
                </form>
              </CardBody>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Change Password</h2>
              </CardHeader>
              <CardBody>
                <form onSubmit={handleChangePassword} className="space-y-4">
                  <Input
                    type="password"
                    label="Current Password"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                    required
                  />
                  <Input
                    type="password"
                    label="New Password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    required
                  />
                  <Input
                    type="password"
                    label="Confirm New Password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    required
                  />
                  <Button type="submit" isLoading={isUpdatingPassword}>
                    Change Password
                  </Button>
                </form>
              </CardBody>
            </Card>
          )}

          {activeTab === 'mfa' && (
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <Shield className="w-5 h-5 mr-2 text-primary-600" />
                  <h2 className="text-lg font-semibold">Two-Factor Authentication</h2>
                </div>
              </CardHeader>
              <CardBody>
                {user?.mfa_enabled ? (
                  <div>
                    <div className="flex items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg mb-4">
                      <div className="w-3 h-3 bg-green-500 rounded-full mr-3" />
                      <span className="text-green-700 dark:text-green-400 font-medium">
                        Two-factor authentication is enabled
                      </span>
                    </div>
                    <Button
                      variant="danger"
                      onClick={async () => {
                        const code = prompt('Enter your MFA code or backup code:');
                        const password = prompt('Enter your password:');
                        if (code && password) {
                          try {
                            await mfaApi.disable(password, code);
                            toast.success('MFA disabled');
                            checkAuth();
                          } catch {
                            toast.error('Failed to disable MFA');
                          }
                        }
                      }}
                    >
                      Disable Two-Factor
                    </Button>
                  </div>
                ) : mfaSetupData ? (
                  <div className="space-y-4">
                    <div className="text-center">
                      <img src={`data:image/png;base64,${mfaSetupData.qr_code}`} alt="QR Code" className="mx-auto w-48 h-48" />
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                        Secret: <code className="bg-gray-100 dark:bg-dark-700 px-2 py-1 rounded">{mfaSetupData.secret}</code>
                      </p>
                    </div>
                    <Input
                      label="Enter 6-digit code"
                      value={mfaCode}
                      onChange={(e) => setMfaCode(e.target.value)}
                      maxLength={6}
                      placeholder="000000"
                    />
                    <Input
                      type="password"
                      label="Enter your password to confirm"
                      value={mfaPassword}
                      onChange={(e) => setMfaPassword(e.target.value)}
                    />
                    <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                      <h4 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Backup Codes</h4>
                      <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-2">
                        Save these codes in a safe place. You can use them to login if you lose access to your authenticator.
                      </p>
                      <ul className="space-y-1">
                        {mfaSetupData.backup_codes.map((code, i) => (
                          <li key={i} className="font-mono text-sm">{code}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="flex space-x-3">
                      <Button onClick={() => setMfaSetupData(null)} variant="ghost">
                        Cancel
                      </Button>
                      <Button onClick={handleEnableMFA} isLoading={!mfaSetupData}>
                        Enable Two-Factor
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Add an extra layer of security to your account by enabling two-factor authentication.
                    </p>
                    <Button onClick={handleSetupMFA}>
                      Set Up Two-Factor Authentication
                    </Button>
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {activeTab === 'backup' && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Backup & Export</h2>
              </CardHeader>
              <CardBody>
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
                    <h4 className="font-medium mb-2">Export Your Vault</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      Download an encrypted backup of all your passwords.
                    </p>
                    <Button variant="secondary">
                      <Download className="w-4 h-4 mr-2" />
                      Export Encrypted Backup
                    </Button>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-dark-700 rounded-lg">
                    <h4 className="font-medium mb-2">Import Backup</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      Restore from a previously exported backup file.
                    </p>
                    <Button variant="secondary">
                      Import Backup
                    </Button>
                  </div>
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}