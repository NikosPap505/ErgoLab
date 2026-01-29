import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotification } from '../components/Notification';

const Warehouses = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [projects, setProjects] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [viewingInventory, setViewingInventory] = useState(null);
  const [addStockModal, setAddStockModal] = useState(null);
  const [transferModal, setTransferModal] = useState(false);
  
  // Data
  const [inventory, setInventory] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  
  const { showNotification } = useNotification();

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    location: '',
    is_central: false,
    project_id: '',
  });

  const [stockFormData, setStockFormData] = useState({
    material_id: '',
    quantity: '',
    transaction_type: 'purchase',
    unit_cost: '',
    notes: '',
  });

  const [transferFormData, setTransferFormData] = useState({
    from_warehouse_id: '',
    to_warehouse_id: '',
    material_id: '',
    quantity: '',
    notes: '',
  });

  const loadData = useCallback(async () => {
    try {
      const [warehousesRes, projectsRes, materialsRes] = await Promise.all([
        api.get('/api/warehouses/'),
        api.get('/api/projects/'),
        api.get('/api/materials/'),
      ]);
      setWarehouses(warehousesRes.data);
      setProjects(projectsRes.data);
      setMaterials(materialsRes.data);
      
      // Load low stock items
      try {
        const lowStockRes = await api.get('/api/inventory/low-stock');
        setLowStockItems(lowStockRes.data);
      } catch (e) {
        // Low stock endpoint might not have data yet
        setLowStockItems([]);
      }
    } catch (error) {
      showNotification('Σφάλμα φόρτωσης δεδομένων', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Warehouse CRUD
  const handleOpenModal = (warehouse = null) => {
    if (warehouse) {
      setEditingWarehouse(warehouse);
      setFormData({
        code: warehouse.code,
        name: warehouse.name,
        location: warehouse.location || '',
        is_central: warehouse.is_central,
        project_id: warehouse.project_id || '',
      });
    } else {
      setEditingWarehouse(null);
      setFormData({
        code: '',
        name: '',
        location: '',
        is_central: false,
        project_id: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingWarehouse(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const data = {
        ...formData,
        project_id: formData.project_id || null,
      };

      if (editingWarehouse) {
        await api.put(`/api/warehouses/${editingWarehouse.id}`, data);
        showNotification('Η αποθήκη ενημερώθηκε επιτυχώς');
      } else {
        await api.post('/api/warehouses/', data);
        showNotification('Η αποθήκη δημιουργήθηκε επιτυχώς');
      }
      
      handleCloseModal();
      loadData();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα αποθήκευσης', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/warehouses/${deleteConfirm.id}`);
      showNotification('Η αποθήκη διαγράφηκε επιτυχώς');
      setDeleteConfirm(null);
      loadData();
    } catch (error) {
      showNotification('Σφάλμα διαγραφής', 'error');
    }
  };

  // Inventory Management
  const handleViewInventory = async (warehouse) => {
    try {
      const response = await api.get(`/api/inventory/warehouse/${warehouse.id}`);
      setInventory(response.data);
      setViewingInventory(warehouse);
    } catch (error) {
      showNotification('Σφάλμα φόρτωσης αποθέματος', 'error');
    }
  };

  const handleOpenAddStock = (warehouse) => {
    setAddStockModal(warehouse);
    setStockFormData({
      material_id: '',
      quantity: '',
      transaction_type: 'purchase',
      unit_cost: '',
      notes: '',
    });
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    
    try {
      await api.post('/api/inventory/transaction', {
        warehouse_id: addStockModal.id,
        material_id: parseInt(stockFormData.material_id),
        transaction_type: stockFormData.transaction_type,
        quantity: parseInt(stockFormData.quantity),
        unit_cost: stockFormData.unit_cost ? parseFloat(stockFormData.unit_cost) : null,
        notes: stockFormData.notes,
      });
      
      showNotification('Η κίνηση αποθέματος καταχωρήθηκε επιτυχώς');
      setAddStockModal(null);
      loadData();
      
      // Refresh inventory if viewing
      if (viewingInventory?.id === addStockModal.id) {
        handleViewInventory(addStockModal);
      }
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα καταχώρησης', 'error');
    }
  };

  const handleOpenTransfer = () => {
    setTransferModal(true);
    setTransferFormData({
      from_warehouse_id: '',
      to_warehouse_id: '',
      material_id: '',
      quantity: '',
      notes: '',
    });
  };

  const handleTransferSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // Create transfer with items
      const transferData = {
        from_warehouse_id: parseInt(transferFormData.from_warehouse_id),
        to_warehouse_id: parseInt(transferFormData.to_warehouse_id),
        items: [
          {
            material_id: parseInt(transferFormData.material_id),
            quantity: parseInt(transferFormData.quantity),
          }
        ],
        notes: transferFormData.notes,
      };

      const response = await api.post('/api/transfers/', transferData);
      
      // Complete the transfer immediately
      await api.put(`/api/transfers/${response.data.id}/complete`);
      
      showNotification('Η μεταφορά ολοκληρώθηκε επιτυχώς');
      setTransferModal(false);
      loadData();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα μεταφοράς', 'error');
    }
  };

  const getStockLevel = (quantity, minLevel) => {
    if (quantity === 0) return { color: 'text-red-600', label: 'Εξαντλημένο' };
    if (quantity <= minLevel) return { color: 'text-orange-600', label: 'Χαμηλό Απόθεμα' };
    return { color: 'text-green-600', label: 'Καλό' };
  };

  if (loading) {
    return <div className="text-center py-12">Φόρτωση...</div>;
  }

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Αποθήκες</h1>
          {lowStockItems.length > 0 && (
            <p className="mt-2 text-sm text-orange-600">
              ⚠️ {lowStockItems.length} υλικά με χαμηλό απόθεμα
            </p>
          )}
        </div>
        <div className="mt-4 sm:mt-0 flex space-x-3">
          <button
            onClick={handleOpenTransfer}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            🚚 Μεταφορά Υλικών
          </button>
          <button
            onClick={() => handleOpenModal()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            + Νέα Αποθήκη
          </button>
        </div>
      </div>

      {/* Low Stock Alert */}
      {lowStockItems.length > 0 && (
        <div className="mb-6 bg-orange-50 border-l-4 border-orange-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-orange-800">Χαμηλό Απόθεμα</h3>
              <div className="mt-2 text-sm text-orange-700">
                <ul className="list-disc list-inside space-y-1">
                  {lowStockItems.slice(0, 5).map((item, index) => (
                    <li key={index}>
                      {item.material_name || item.material?.name} - {item.warehouse_name || item.warehouse?.name}: {item.quantity} τεμ.
                    </li>
                  ))}
                </ul>
                {lowStockItems.length > 5 && (
                  <p className="mt-2 text-xs">και {lowStockItems.length - 5} ακόμα...</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Warehouses Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {warehouses.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-gray-500">
            Δεν υπάρχουν αποθήκες
          </div>
        ) : (
          warehouses.map((warehouse) => (
            <div key={warehouse.id} className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow">
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">{warehouse.name}</h3>
                  {warehouse.is_central && (
                    <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                      Κεντρική
                    </span>
                  )}
                </div>
                <dl className="space-y-2">
                  <div>
                    <dt className="text-sm text-gray-500">Κωδικός</dt>
                    <dd className="text-sm font-medium text-gray-900">{warehouse.code}</dd>
                  </div>
                  {warehouse.location && (
                    <div>
                      <dt className="text-sm text-gray-500">Τοποθεσία</dt>
                      <dd className="text-sm font-medium text-gray-900">{warehouse.location}</dd>
                    </div>
                  )}
                </dl>
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleViewInventory(warehouse)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    📦 Απόθεμα
                  </button>
                  <button
                    onClick={() => handleOpenAddStock(warehouse)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-primary-600 hover:bg-gray-50"
                  >
                    + Κίνηση
                  </button>
                  <button
                    onClick={() => handleOpenModal(warehouse)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-600 hover:bg-gray-50"
                  >
                    ✏️ Επεξ.
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(warehouse)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-red-600 hover:bg-gray-50"
                  >
                    🗑️ Διαγρ.
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create/Edit Warehouse Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingWarehouse ? 'Επεξεργασία Αποθήκης' : 'Νέα Αποθήκη'}
      >
        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Κωδικός *</label>
              <input
                type="text"
                required
                value={formData.code}
                onChange={(e) => setFormData({...formData, code: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Όνομα *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Τοποθεσία</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.is_central}
                  onChange={(e) => setFormData({...formData, is_central: e.target.checked, project_id: e.target.checked ? '' : formData.project_id})}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">Κεντρική Αποθήκη</span>
              </label>
            </div>
            {!formData.is_central && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Έργο</label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData({...formData, project_id: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                >
                  <option value="">-- Χωρίς έργο --</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.code} - {project.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              {editingWarehouse ? 'Ενημέρωση' : 'Δημιουργία'}
            </button>
            <button
              type="button"
              onClick={handleCloseModal}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
            >
              Ακύρωση
            </button>
          </div>
        </form>
      </Modal>

      {/* View Inventory Modal */}
      <Modal
        isOpen={!!viewingInventory}
        onClose={() => setViewingInventory(null)}
        title={`Απόθεμα - ${viewingInventory?.name}`}
        size="lg"
      >
        {inventory.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Δεν υπάρχουν υλικά σε αυτή την αποθήκη</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Υλικό</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Ποσότητα</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">Κατάσταση</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {inventory.map((item) => {
                  const material = materials.find(m => m.id === item.material_id);
                  const stockLevel = getStockLevel(item.quantity, material?.min_stock_level || 0);
                  
                  return (
                    <tr key={item.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.material_sku || material?.sku}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.material_name || material?.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className={`text-xs font-semibold ${stockLevel.color}`}>
                          {stockLevel.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Modal>

      {/* Add Stock Transaction Modal */}
      <Modal
        isOpen={!!addStockModal}
        onClose={() => setAddStockModal(null)}
        title={`Κίνηση Αποθέματος - ${addStockModal?.name}`}
        size="md"
      >
        <form onSubmit={handleAddStock}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Τύπος Κίνησης *</label>
              <select
                required
                value={stockFormData.transaction_type}
                onChange={(e) => setStockFormData({...stockFormData, transaction_type: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="purchase">Αγορά/Προσθήκη</option>
                <option value="consumption">Κατανάλωση</option>
                <option value="return">Επιστροφή</option>
                <option value="adjustment">Διόρθωση</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Υλικό *</label>
              <select
                required
                value={stockFormData.material_id}
                onChange={(e) => setStockFormData({...stockFormData, material_id: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="">-- Επιλέξτε υλικό --</option>
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.sku} - {material.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Ποσότητα * {stockFormData.transaction_type === 'consumption' && '(θα αφαιρεθεί)'}
              </label>
              <input
                type="number"
                required
                min="1"
                value={stockFormData.quantity}
                onChange={(e) => setStockFormData({...stockFormData, quantity: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>

            {stockFormData.transaction_type === 'purchase' && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Τιμή Μονάδας (€)</label>
                <input
                  type="number"
                  step="0.01"
                  value={stockFormData.unit_cost}
                  onChange={(e) => setStockFormData({...stockFormData, unit_cost: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700">Σημειώσεις</label>
              <textarea
                rows="3"
                value={stockFormData.notes}
                onChange={(e) => setStockFormData({...stockFormData, notes: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Καταχώρηση
            </button>
            <button
              type="button"
              onClick={() => setAddStockModal(null)}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
            >
              Ακύρωση
            </button>
          </div>
        </form>
      </Modal>

      {/* Transfer Modal */}
      <Modal
        isOpen={transferModal}
        onClose={() => setTransferModal(false)}
        title="Μεταφορά Υλικών"
        size="md"
      >
        <form onSubmit={handleTransferSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Από Αποθήκη *</label>
              <select
                required
                value={transferFormData.from_warehouse_id}
                onChange={(e) => setTransferFormData({...transferFormData, from_warehouse_id: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="">-- Επιλέξτε αποθήκη --</option>
                {warehouses.map((wh) => (
                  <option key={wh.id} value={wh.id}>
                    {wh.code} - {wh.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="text-center text-2xl">⬇️</div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Προς Αποθήκη *</label>
              <select
                required
                value={transferFormData.to_warehouse_id}
                onChange={(e) => setTransferFormData({...transferFormData, to_warehouse_id: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="">-- Επιλέξτε αποθήκη --</option>
                {warehouses
                  .filter(wh => wh.id !== parseInt(transferFormData.from_warehouse_id))
                  .map((wh) => (
                    <option key={wh.id} value={wh.id}>
                      {wh.code} - {wh.name}
                    </option>
                  ))}
              </select>
            </div>

            <div className="border-t pt-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Υλικό *</label>
                <select
                  required
                  value={transferFormData.material_id}
                  onChange={(e) => setTransferFormData({...transferFormData, material_id: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                >
                  <option value="">-- Επιλέξτε υλικό --</option>
                  {materials.map((material) => (
                    <option key={material.id} value={material.id}>
                      {material.sku} - {material.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Ποσότητα *</label>
                <input
                  type="number"
                  required
                  min="1"
                  value={transferFormData.quantity}
                  onChange={(e) => setTransferFormData({...transferFormData, quantity: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700">Σημειώσεις</label>
                <textarea
                  rows="2"
                  value={transferFormData.notes}
                  onChange={(e) => setTransferFormData({...transferFormData, notes: e.target.value})}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                />
              </div>
            </div>
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Μεταφορά
            </button>
            <button
              type="button"
              onClick={() => setTransferModal(false)}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:w-auto sm:text-sm"
            >
              Ακύρωση
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDelete}
        title="Διαγραφή Αποθήκης"
        message={`Είστε σίγουροι ότι θέλετε να διαγράψετε την αποθήκη "${deleteConfirm?.name}";`}
      />
    </div>
  );
};

export default Warehouses;
