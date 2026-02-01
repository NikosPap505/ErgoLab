import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '../components/Notification';
import api from '../services/api';
import {
  ArrowsRightLeftIcon,
  PlusIcon,
  CheckIcon,
  XMarkIcon,
  TruckIcon,
  ClockIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const Transfers = () => {
  const { t } = useTranslation();
  const { showSuccess, showError } = useNotification();
  
  const [transfers, setTransfers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  const [formData, setFormData] = useState({
    from_warehouse_id: '',
    to_warehouse_id: '',
    material_id: '',
    quantity: '',
    notes: ''
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [transfersRes, warehousesRes, materialsRes] = await Promise.all([
        api.get('/api/transfers/'),
        api.get('/api/warehouses/'),
        api.get('/api/materials/')
      ]);
      setTransfers(transfersRes.data);
      setWarehouses(warehousesRes.data);
      setMaterials(materialsRes.data.items || materialsRes.data);
    } catch (error) {
      showError(t('transfers.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [showError, t]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/api/transfers/', formData);
      showSuccess(t('transfers.messages.createSuccess'));
      setIsModalOpen(false);
      setFormData({
        from_warehouse_id: '',
        to_warehouse_id: '',
        material_id: '',
        quantity: '',
        notes: ''
      });
      fetchData();
    } catch (error) {
      showError(error.response?.data?.detail || t('transfers.messages.createError'));
    }
  };

  const handleStatusUpdate = async (transferId, newStatus) => {
    try {
      await api.patch(`/api/transfers/${transferId}`, { status: newStatus });
      showSuccess(t('transfers.messages.updateSuccess'));
      fetchData();
    } catch (error) {
      showError(t('transfers.messages.updateError'));
    }
  };

  const filteredTransfers = transfers.filter(transfer => {
    const matchesSearch = 
      transfer.material?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transfer.from_warehouse?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      transfer.to_warehouse?.name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || transfer.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_transit: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || styles.pending}`}>
        {t(`transfers.status.${status}`)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('transfers.title')}</h1>
          <p className="text-gray-500">{t('transfers.subtitle')}</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          {t('transfers.createNew')}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder={t('transfers.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="all">{t('transfers.allStatus')}</option>
          <option value="pending">{t('transfers.status.pending')}</option>
          <option value="in_transit">{t('transfers.status.in_transit')}</option>
          <option value="completed">{t('transfers.status.completed')}</option>
          <option value="cancelled">{t('transfers.status.cancelled')}</option>
        </select>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: t('transfers.stats.total'), value: transfers.length, icon: ArrowsRightLeftIcon, color: 'blue' },
          { label: t('transfers.stats.pending'), value: transfers.filter(transfer => transfer.status === 'pending').length, icon: ClockIcon, color: 'yellow' },
          { label: t('transfers.stats.inTransit'), value: transfers.filter(transfer => transfer.status === 'in_transit').length, icon: TruckIcon, color: 'purple' },
          { label: t('transfers.stats.completed'), value: transfers.filter(transfer => transfer.status === 'completed').length, icon: CheckIcon, color: 'green' }
        ].map((stat, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg bg-${stat.color}-100`}>
                <stat.icon className={`h-6 w-6 text-${stat.color}-600`} />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Transfers List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.material')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.from')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.to')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.quantity')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.status')}</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('transfers.table.date')}</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('transfers.table.actions')}</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredTransfers.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                  {t('transfers.noTransfersFound')}
                </td>
              </tr>
            ) : (
              filteredTransfers.map((transfer) => (
                <tr key={transfer.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{transfer.material?.name || 'N/A'}</div>
                    <div className="text-sm text-gray-500">{transfer.material?.sku || ''}</div>
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {transfer.from_warehouse?.name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {transfer.to_warehouse?.name || 'N/A'}
                  </td>
                  <td className="px-6 py-4 font-medium">{transfer.quantity}</td>
                  <td className="px-6 py-4">{getStatusBadge(transfer.status)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(transfer.transfer_date || transfer.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {transfer.status === 'pending' && (
                      <>
                        <button
                          onClick={() => handleStatusUpdate(transfer.id, 'in_transit')}
                          className="text-blue-600 hover:text-blue-800"
                          title={t('transfers.actions.markInTransit')}
                        >
                          <TruckIcon className="h-5 w-5 inline" />
                        </button>
                        <button
                          onClick={() => handleStatusUpdate(transfer.id, 'cancelled')}
                          className="text-red-600 hover:text-red-800"
                          title={t('transfers.actions.cancel')}
                        >
                          <XMarkIcon className="h-5 w-5 inline" />
                        </button>
                      </>
                    )}
                    {transfer.status === 'in_transit' && (
                      <button
                        onClick={() => handleStatusUpdate(transfer.id, 'completed')}
                        className="text-green-600 hover:text-green-800"
                        title={t('transfers.actions.markCompleted')}
                      >
                        <CheckIcon className="h-5 w-5 inline" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Transfer Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">{t('transfers.form.title')}</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-500 hover:text-gray-700">
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('transfers.form.fromWarehouse')}</label>
                <select
                  value={formData.from_warehouse_id}
                  onChange={(e) => setFormData({ ...formData, from_warehouse_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">{t('transfers.form.selectSourceWarehouse')}</option>
                  {warehouses.map(w => (
                    <option key={w.id} value={w.id}>{w.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('transfers.form.toWarehouse')}</label>
                <select
                  value={formData.to_warehouse_id}
                  onChange={(e) => setFormData({ ...formData, to_warehouse_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">{t('transfers.form.selectDestinationWarehouse')}</option>
                  {warehouses
                    .filter(w => w.id !== parseInt(formData.from_warehouse_id))
                    .map(w => (
                      <option key={w.id} value={w.id}>{w.name}</option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('transfers.form.material')}</label>
                <select
                  value={formData.material_id}
                  onChange={(e) => setFormData({ ...formData, material_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                >
                  <option value="">{t('transfers.form.selectMaterial')}</option>
                  {materials.map(m => (
                    <option key={m.id} value={m.id}>{m.name} ({m.sku})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('transfers.form.quantity')}</label>
                <input
                  type="number"
                  min="1"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('transfers.form.notes')}</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  rows="3"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  {t('common.cancel')}
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  {t('transfers.form.createTransfer')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Transfers;
