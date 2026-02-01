import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotification } from '../components/Notification';
import { usePermissions } from '../context/PermissionContext';
import PermissionGate from '../components/PermissionGate';
import RoleBadge from '../components/RoleBadge';

const Users = () => {
  const { t } = useTranslation();
  const { showNotification } = useNotification();
  const { hasPermission } = usePermissions();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const canCreate = hasPermission('user:create');
  const canUpdate = hasPermission('user:update');
  const canDelete = hasPermission('user:delete');
  const canManageRoles = hasPermission('user:manage_roles');

  const [formData, setFormData] = useState({
    username: '',
    full_name: '',
    email: '',
    phone: '',
    address: '',
    role: 'worker',
    is_active: true,
    password: '',
  });

  const roles = useMemo(
    () => [
      { value: 'admin', label: t('roles.admin') },
      { value: 'manager', label: t('roles.manager') },
      { value: 'supervisor', label: t('roles.supervisor') },
      { value: 'worker', label: t('roles.worker') },
      { value: 'viewer', label: t('roles.viewer') },
    ],
    [t]
  );

  const loadUsers = useCallback(async () => {
    try {
      const response = await api.get('/api/users/');
      setUsers(response.data);
    } catch (error) {
      showNotification(t('errors.loadUsers'), 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification, t]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleOpenModal = (user = null) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username || '',
        full_name: user.full_name || '',
        email: user.email || '',
        phone: user.phone || '',
        address: user.address || '',
        role: user.role || 'worker',
        is_active: user.is_active ?? true,
        password: '',
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        full_name: '',
        email: '',
        phone: '',
        address: '',
        role: 'worker',
        is_active: true,
        password: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingUser(null);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      if (editingUser) {
        if (!canUpdate) {
          showNotification(t('errors.noPermission'), 'error');
          return;
        }

        const updatePayload = {
          email: formData.email || null,
          full_name: formData.full_name || null,
          phone: formData.phone || null,
          address: formData.address || null,
          is_active: formData.is_active,
        };

        if (formData.password) {
          updatePayload.password = formData.password;
        }

        if (canManageRoles && formData.role !== editingUser.role) {
          await api.post('/api/users/change-role', {
            user_id: editingUser.id,
            new_role: formData.role,
          });
        }

        await api.put(`/api/users/${editingUser.id}`, updatePayload);
        showNotification(t('messages.saveSuccess'));
      } else {
        if (!canCreate) {
          showNotification(t('errors.noPermission'), 'error');
          return;
        }

        await api.post('/api/users/', {
          username: formData.username,
          email: formData.email || null,
          full_name: formData.full_name || null,
          phone: formData.phone || null,
          address: formData.address || null,
          role: formData.role,
          password: formData.password,
        });
        showNotification(t('messages.saveSuccess'));
      }

      handleCloseModal();
      loadUsers();
    } catch (error) {
      showNotification(error.response?.data?.detail || t('errors.saveUser'), 'error');
    }
  };

  const handleDelete = async () => {
    try {
      if (!canDelete) {
        showNotification(t('errors.noPermission'), 'error');
        return;
      }

      await api.delete(`/api/users/${deleteConfirm.id}`);
      showNotification(t('messages.deleteSuccess'));
      setDeleteConfirm(null);
      loadUsers();
    } catch (error) {
      showNotification(error.response?.data?.detail || t('errors.deleteUser'), 'error');
    }
  };

  const filteredUsers = users.filter((user) => {
    const term = searchTerm.toLowerCase();
    return (
      user.username?.toLowerCase().includes(term) ||
      user.full_name?.toLowerCase().includes(term) ||
      user.email?.toLowerCase().includes(term)
    );
  });

  if (loading) {
    return <div className="text-center py-12">{t('common.loading')}</div>;
  }

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{t('users.title')}</h1>
        <PermissionGate permission="user:create">
          <button
            onClick={() => handleOpenModal()}
            className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            + {t('users.createNew')}
          </button>
        </PermissionGate>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder={t('users.searchPlaceholder')}
          value={searchTerm}
          onChange={(event) => setSearchTerm(event.target.value)}
          className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
        />
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('users.fields.username')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('users.fields.fullName')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('users.fields.email')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('users.fields.role')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('users.fields.status')}
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('common.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredUsers.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                  {t('users.noUsers')}
                </td>
              </tr>
            ) : (
              filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {user.username}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.full_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.email || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <RoleBadge role={user.role} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {user.is_active ? t('users.active') : t('users.inactive')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <PermissionGate permission={['user:update', 'user:manage_roles']}>
                      <button
                        onClick={() => handleOpenModal(user)}
                        className="text-primary-600 hover:text-primary-900 mr-4"
                      >
                        {t('common.edit')}
                      </button>
                    </PermissionGate>
                    <PermissionGate permission="user:delete">
                      <button
                        onClick={() => setDeleteConfirm(user)}
                        className="text-red-600 hover:text-red-900"
                      >
                        {t('common.delete')}
                      </button>
                    </PermissionGate>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingUser ? t('users.editUser') : t('users.createNew')}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.username')} *
              </label>
              <input
                type="text"
                required
                disabled={!!editingUser}
                value={formData.username}
                onChange={(event) =>
                  setFormData({ ...formData, username: event.target.value })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.fullName')}
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(event) =>
                  setFormData({ ...formData, full_name: event.target.value })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.email')}
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(event) =>
                  setFormData({ ...formData, email: event.target.value })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.phone')}
              </label>
              <input
                type="text"
                value={formData.phone}
                onChange={(event) =>
                  setFormData({ ...formData, phone: event.target.value })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.address')}
              </label>
              <input
                type="text"
                value={formData.address}
                onChange={(event) =>
                  setFormData({ ...formData, address: event.target.value })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.role')}
              </label>
              <select
                value={formData.role}
                onChange={(event) =>
                  setFormData({ ...formData, role: event.target.value })
                }
                disabled={!canManageRoles}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
              {!canManageRoles && (
                <p className="text-xs text-gray-500 mt-1">
                  {t('users.rolePermissionHint')}
                </p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.status')}
              </label>
              <select
                value={formData.is_active ? 'active' : 'inactive'}
                onChange={(event) =>
                  setFormData({
                    ...formData,
                    is_active: event.target.value === 'active',
                  })
                }
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="active">{t('users.active')}</option>
                <option value="inactive">{t('users.inactive')}</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                {t('users.fields.password')}
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(event) =>
                  setFormData({ ...formData, password: event.target.value })
                }
                required={!editingUser}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
              {editingUser && (
                <p className="text-xs text-gray-500 mt-1">
                  {t('users.passwordHint')}
                </p>
              )}
            </div>
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleCloseModal}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {t('common.cancel')}
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
            >
              {t('common.save')}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDelete}
        title={t('common.delete')}
        message={t('messages.deleteConfirm')}
        confirmText={t('common.delete')}
        cancelText={t('common.cancel')}
      />
    </div>
  );
};

export default Users;
