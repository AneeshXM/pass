import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { vaultsApi, credentialsApi } from '@/services/api';
import { Card, CardBody, Button, Input, Modal, Spinner } from '@/components/ui';
import {
  Plus,
  Search,
  Lock,
  Copy,
  Eye,
  EyeOff,
  Star,
  StarOff,
  Edit,
  Trash2,
  ArrowLeft,
  Link as LinkIcon,
  MoreVertical,
} from 'lucide-react';
import toast from 'react-hot-toast';
import type { Vault, Credential, CredentialCreate, CredentialDetail } from '@/types';

export function VaultDetailPage() {
  const { vaultId } = useParams<{ vaultId: string }>();
  const [vault, setVault] = useState<Vault | null>(null);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [visiblePasswords, setVisiblePasswords] = useState<Record<number, string>>({});
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Form state
  const [newCredName, setNewCredName] = useState('');
  const [newCredUrl, setNewCredUrl] = useState('');
  const [newCredUsername, setNewCredUsername] = useState('');
  const [newCredPassword, setNewCredPassword] = useState('');
  const [newCredNotes, setNewCredNotes] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (vaultId) {
      loadVault();
      loadCredentials();
    }
  }, [vaultId]);

  const loadVault = async () => {
    try {
      const data = await vaultsApi.get(Number(vaultId));
      setVault(data);
    } catch (error) {
      console.error('Failed to load vault:', error);
      toast.error('Failed to load vault');
    }
  };

  const loadCredentials = async () => {
    try {
      setIsLoading(true);
      const response = await credentialsApi.list(Number(vaultId), {
        search: search || undefined,
      });
      setCredentials(response.items);
    } catch (error) {
      console.error('Failed to load credentials:', error);
      toast.error('Failed to load credentials');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async (text: string, id: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      toast.success('Copied to clipboard');
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  const handleTogglePassword = async (credentialId: number) => {
    if (visiblePasswords[credentialId]) {
      const newVisible = { ...visiblePasswords };
      delete newVisible[credentialId];
      setVisiblePasswords(newVisible);
    } else {
      try {
        const detail = await credentialsApi.getWithPassword(credentialId);
        setVisiblePasswords({ ...visiblePasswords, [credentialId]: detail.password });
      } catch (error) {
        toast.error('Failed to get password');
      }
    }
  };

  const handleToggleFavorite = async (credentialId: number) => {
    try {
      const result = await credentialsApi.toggleFavorite(credentialId);
      setCredentials(
        credentials.map((c) =>
          c.id === credentialId ? { ...c, favorite: result.favorite } : c
        )
      );
    } catch (error) {
      toast.error('Failed to toggle favorite');
    }
  };

  const handleCreateCredential = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCredName.trim() || !newCredPassword.trim()) return;

    setIsCreating(true);
    try {
      await credentialsApi.create({
        name: newCredName,
        url: newCredUrl || undefined,
        username: newCredUsername || undefined,
        password: newCredPassword,
        notes: newCredNotes || undefined,
        vault_id: Number(vaultId),
      });
      toast.success('Credential created successfully');
      setShowCreateModal(false);
      resetForm();
      loadCredentials();
    } catch (error) {
      toast.error('Failed to create credential');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteCredential = async (credentialId: number) => {
    if (!confirm('Are you sure you want to delete this credential?')) return;

    try {
      await credentialsApi.delete(credentialId);
      toast.success('Credential deleted');
      loadCredentials();
    } catch (error) {
      toast.error('Failed to delete credential');
    }
  };

  const resetForm = () => {
    setNewCredName('');
    setNewCredUrl('');
    setNewCredUsername('');
    setNewCredPassword('');
    setNewCredNotes('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link
            to="/vaults"
            className="p-2 mr-2 hover:bg-gray-100 dark:hover:bg-dark-700 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {vault?.name || 'Vault'}
            </h1>
            {vault?.description && (
              <p className="text-gray-500 dark:text-gray-400 mt-1">
                {vault.description}
              </p>
            )}
          </div>
        </div>
        <Button onClick={() => setShowCreateModal(true)} leftIcon={<Plus className="w-5 h-5" />}>
          Add Password
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search passwords..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Credentials List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Spinner size="lg" />
        </div>
      ) : credentials.length === 0 ? (
        <Card>
          <CardBody className="text-center py-12">
            <Lock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              No passwords yet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              Add your first password to this vault
            </p>
            <Button onClick={() => setShowCreateModal(true)}>Add Password</Button>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {credentials.map((cred) => (
            <Card key={cred.id}>
              <CardBody>
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="w-10 h-10 bg-gray-100 dark:bg-dark-700 rounded-lg flex items-center justify-center mr-3">
                      <Lock className="w-5 h-5 text-gray-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                          {cred.name}
                        </h3>
                        {cred.favorite && (
                          <Star className="w-4 h-4 text-yellow-500 ml-2" fill="currentColor" />
                        )}
                      </div>
                      {cred.username && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {cred.username}
                        </p>
                      )}
                      {cred.url && (
                        <p className="text-xs text-gray-400 dark:text-gray-500 truncate flex items-center mt-1">
                          <LinkIcon className="w-3 h-3 mr-1" />
                          {cred.url}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {cred.username && (
                      <button
                        onClick={() => handleCopy(cred.username!, cred.id)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="Copy username"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleTogglePassword(cred.id)}
                      className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      title={visiblePasswords[cred.id] ? 'Hide password' : 'Show password'}
                    >
                      {visiblePasswords[cred.id] ? (
                        <EyeOff className="w-4 h-4" />
                      ) : (
                        <Eye className="w-4 h-4" />
                      )}
                    </button>
                    {visiblePasswords[cred.id] && (
                      <button
                        onClick={() => handleCopy(visiblePasswords[cred.id], cred.id)}
                        className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="Copy password"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleToggleFavorite(cred.id)}
                      className="p-2 text-gray-400 hover:text-yellow-500"
                      title={cred.favorite ? 'Remove from favorites' : 'Add to favorites'}
                    >
                      {cred.favorite ? (
                        <Star className="w-4 h-4" fill="currentColor" />
                      ) : (
                        <StarOff className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteCredential(cred.id)}
                      className="p-2 text-gray-400 hover:text-red-600"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {/* Create Credential Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Add New Password"
        size="lg"
      >
        <form onSubmit={handleCreateCredential} className="space-y-4">
          <Input
            label="Name"
            placeholder="e.g., Gmail"
            value={newCredName}
            onChange={(e) => setNewCredName(e.target.value)}
            required
          />
          <Input
            label="URL (optional)"
            placeholder="https://example.com"
            value={newCredUrl}
            onChange={(e) => setNewCredUrl(e.target.value)}
          />
          <Input
            label="Username / Email (optional)"
            placeholder="user@example.com"
            value={newCredUsername}
            onChange={(e) => setNewCredUsername(e.target.value)}
          />
          <Input
            label="Password"
            type="password"
            placeholder="Enter password"
            value={newCredPassword}
            onChange={(e) => setNewCredPassword(e.target.value)}
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Notes (optional)
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              placeholder="Additional notes..."
              value={newCredNotes}
              onChange={(e) => setNewCredNotes(e.target.value)}
            />
          </div>
          <div className="flex justify-end space-x-3">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Save Password
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}