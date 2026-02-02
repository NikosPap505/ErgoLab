import React, { useEffect, useState, useCallback } from 'react';
import api from '../services/api';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotification } from '../components/Notification';

const Materials = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMaterial, setEditingMaterial] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [qrCode, setQrCode] = useState(null);
  const [showQRModal, setShowQRModal] = useState(false);
  const [isQrLoading, setIsQrLoading] = useState(false);
  const { showNotification } = useNotification();

  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    category: '',
    unit: 'piece',
    unit_price: '',
    min_stock_level: '0',
    barcode: '',
    supplier: '',
  });

  const loadMaterials = useCallback(async () => {
    try {
      const response = await api.get('/api/materials/');
      setMaterials(response.data);
    } catch (_error) {
      showNotification('Σφάλμα φόρτωσης υλικών', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  useEffect(() => {
    loadMaterials();
  }, [loadMaterials]);

  const handleOpenModal = (material = null) => {
    if (material) {
      setEditingMaterial(material);
      setFormData(material);
    } else {
      setEditingMaterial(null);
      setFormData({
        sku: '',
        name: '',
        description: '',
        category: '',
        unit: 'piece',
        unit_price: '',
        min_stock_level: '0',
        barcode: '',
        supplier: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingMaterial(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (editingMaterial) {
        await api.put(`/api/materials/${editingMaterial.id}`, formData);
        showNotification('Το υλικό ενημερώθηκε επιτυχώς');
      } else {
        await api.post('/api/materials/', formData);
        showNotification('Το υλικό δημιουργήθηκε επιτυχώς');
      }
      
      handleCloseModal();
      loadMaterials();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα αποθήκευσης', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/materials/${deleteConfirm.id}`);
      showNotification('Το υλικό διαγράφηκε επιτυχώς');
      setDeleteConfirm(null);
      loadMaterials();
    } catch (_error) {
      showNotification('Σφάλμα διαγραφής', 'error');
    }
  };

  const handleGenerateQR = async (material) => {
    setIsQrLoading(true);
    try {
      const response = await api.get(`/api/materials/${material.id}/qr`);
      setQrCode(response.data.qr_code);
      setSelectedMaterial(material);
      setShowQRModal(true);
    } catch (_error) {
      showNotification('Σφάλμα δημιουργίας QR', 'error');
    } finally {
      setIsQrLoading(false);
    }
  };

  const handlePrintLabel = async (material) => {
    try {
      const response = await api.get(
        `/api/materials/${material.id}/qr?printable=true&format=png`,
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], { type: 'image/png' });
      const url = URL.createObjectURL(blob);

      const printWindow = window.open(url, '_blank');
      if (printWindow) {
        printWindow.addEventListener('load', () => {
          printWindow.print();
        });
      }
    } catch (_error) {
      showNotification('Σφάλμα εκτύπωσης ετικέτας', 'error');
    }
  };

  const filteredMaterials = materials.filter(m =>
    m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    m.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="text-center py-12">Φόρτωση...</div>;
  }

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Υλικά</h1>
        <button
          onClick={() => handleOpenModal()}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
        >
          + Νέο Υλικό
        </button>
      </div>

      {/* Search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Αναζήτηση υλικών..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="shadow-sm focus:ring-primary-500 focus:border-primary-500 block w-full sm:text-sm border-gray-300 rounded-md p-2 border"
        />
      </div>

      {/* Table */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Όνομα</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Κατηγορία</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Τιμή</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Μονάδα</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ενέργειες</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredMaterials.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                  Δεν βρέθηκαν υλικά
                </td>
              </tr>
            ) : (
              filteredMaterials.map((material) => (
                <tr key={material.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{material.sku}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{material.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      {material.category || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    €{material.unit_price || '0.00'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{material.unit}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleOpenModal(material)}
                      className="text-primary-600 hover:text-primary-900 mr-4"
                    >
                      Επεξεργασία
                    </button>
                    <button
                      onClick={() => handleGenerateQR(material)}
                      className="text-indigo-600 hover:text-indigo-900 mr-4"
                      disabled={isQrLoading}
                    >
                      📱 QR
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(material)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Διαγραφή
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingMaterial ? 'Επεξεργασία Υλικού' : 'Νέο Υλικό'}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">SKU *</label>
              <input
                type="text"
                required
                value={formData.sku}
                onChange={(e) => setFormData({...formData, sku: e.target.value})}
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
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">Περιγραφή</label>
              <textarea
                rows="3"
                value={formData.description || ''}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Κατηγορία</label>
              <input
                type="text"
                value={formData.category || ''}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Μονάδα Μέτρησης</label>
              <select
                value={formData.unit}
                onChange={(e) => setFormData({...formData, unit: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="piece">Τεμάχια</option>
                <option value="meter">Μέτρα</option>
                <option value="kilogram">Κιλά</option>
                <option value="liter">Λίτρα</option>
                <option value="box">Κουτιά</option>
                <option value="package">Πακέτα</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Τιμή Μονάδας (€)</label>
              <input
                type="number"
                step="0.01"
                value={formData.unit_price || ''}
                onChange={(e) => setFormData({...formData, unit_price: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Ελάχιστο Απόθεμα</label>
              <input
                type="number"
                value={formData.min_stock_level || ''}
                onChange={(e) => setFormData({...formData, min_stock_level: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Barcode</label>
              <input
                type="text"
                value={formData.barcode || ''}
                onChange={(e) => setFormData({...formData, barcode: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700">Προμηθευτής</label>
              <input
                type="text"
                value={formData.supplier || ''}
                onChange={(e) => setFormData({...formData, supplier: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              {editingMaterial ? 'Ενημέρωση' : 'Δημιουργία'}
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

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDelete}
        title="Διαγραφή Υλικού"
        message={`Είστε σίγουροι ότι θέλετε να διαγράψετε το υλικό "${deleteConfirm?.name}";`}
      />

      {showQRModal && selectedMaterial && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">{selectedMaterial.name}</h3>
            {qrCode ? (
              <img src={qrCode} alt="QR Code" className="w-full" />
            ) : (
              <div className="text-center py-12">Φόρτωση QR...</div>
            )}
            <p className="text-center text-sm text-gray-600 mt-4">
              SKU: {selectedMaterial.sku}
            </p>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowQRModal(false)}
                className="btn-secondary flex-1"
              >
                Κλείσιμο
              </button>
              <button
                onClick={() => handlePrintLabel(selectedMaterial)}
                className="btn-primary flex-1"
              >
                🖨️ Print
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Materials;
