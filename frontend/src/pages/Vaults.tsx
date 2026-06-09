import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { vaultsApi } from '@/services/api';
import { Card, CardBody, Button, Input, Modal, Spinner } from '@/components/ui';
import { Plus, Search, Folder, Lock, Share2, MoreVertical, Edit, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';
import type { Vault, VaultCreate } from '@/types';

export function VaultsPage() {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newVaultName, setNewVaultName] = useState('');
  const [newVaultDescription, setNewVaultDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadVaults();
  }, [search]);

  const loadVaults = async () => {
    try {
      setIsLoading(true);
      const response = await vaultsApi.list({ search: search || undefined });
      setVaults(response.items);
    } catch (error) {
      console.error('Failed to load vaults:', error);
      toast.error('Failed to load vaults');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateVault = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVaultName.trim()) return;

    setIsCreating(true);
    try {
      await vaultsApi.create({
        name: newVaultName,
        description: newVaultDescription || undefined,
      });
      toast.success('Vault created successfully');
      setShowCreateModal(false);
      setNewVaultName('');
      setNewVaultDescription('');
      loadVaults();
    } catch (error) {
      toast.error('Failed to create vault');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteVault = async (vaultId: number) => {
    if (!confirm('Are you sure you want to delete this vault?')) return;

    try {
      await vaultsApi.delete(vaultId);
      toast.success('Vault deleted successfully');
      loadVaults();
    } catch (error) {
      toast.error('Failed to delete vault');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            My Vaults
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Organize your passwords into vaults
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} leftIcon={<Plus className="w-5 h-5" />}>
          New Vault
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search vaults..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Vaults Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Spinner size="lg" />
        </div>
      ) : vaults.length === 0 ? (
        <Card>
          <CardBody className="text-center py-12">
            <Folder className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              No vaults found
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {search ? 'Try a different search term' : 'Create your first vault to get started'}
            </p>
            {!search && (
              <Button onClick={() => setShowCreateModal(true)}>
                Create Vault
              </Button>
            )}
          </CardBody>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vaults.map((vault) => (
            <Card key={vault.id}>
              <CardBody>
                <div className="flex items-start justify-between">
                  <Link to={`/vaults/${vault.id}`} className="flex items-start flex-1">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center mr-3"
                      style={{ backgroundColor: vault.color || '#0ea5e9' }}
                    >
                      <Folder className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
                        {vault.name}
                      </h3>
                      {vault.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-1">
                          {vault.description}
                        </p>
                      )}
                    </div>
                  </Link>
                  <div className="flex items-center space-x-1">
                    {vault.is_shared && (
                      <Share2 className="w-4 h-4 text-primary-600" />
                    )}
                    <button
                      onClick={() => handleDeleteVault(vault.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
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

      {/* Create Vault Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Vault"
      >
        <form onSubmit={handleCreateVault} className="space-y-4">
          <Input
            label="Vault Name"
            placeholder="e.g., Work Accounts"
            value={newVaultName}
            onChange={(e) => setNewVaultName(e.target.value)}
            required
          />
          <Input
            label="Description (optional)"
            placeholder="Brief description of this vault"
            value={newVaultDescription}
            onChange={(e) => setNewVaultDescription(e.target.value)}
          />
          <div className="flex justify-end space-x-3">
            <Button variant="ghost" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isCreating}>
              Create Vault
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}