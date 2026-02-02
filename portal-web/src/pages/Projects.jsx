import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotification } from '../components/Notification';

const Projects = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const { showNotification } = useNotification();

  const [formData, setFormData] = useState({
    code: '',
    name: '',
    description: '',
    location: '',
    client_name: '',
    status: 'planning',
    budget: '',
    start_date: '',
    end_date: '',
  });

  const loadProjects = useCallback(async () => {
    try {
      const response = await api.get('/api/projects/');
      setProjects(response.data);
    } catch (_error) {
      showNotification('Σφάλμα φόρτωσης έργων', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  const handleOpenModal = (project = null) => {
    if (project) {
      setEditingProject(project);
      setFormData({
        ...project,
        start_date: project.start_date ? project.start_date.split('T')[0] : '',
        end_date: project.end_date ? project.end_date.split('T')[0] : '',
      });
    } else {
      setEditingProject(null);
      setFormData({
        code: '',
        name: '',
        description: '',
        location: '',
        client_name: '',
        status: 'planning',
        budget: '',
        start_date: '',
        end_date: '',
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProject(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const data = {
        ...formData,
        budget: formData.budget ? parseFloat(formData.budget) : null,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null,
      };

      if (editingProject) {
        await api.put(`/api/projects/${editingProject.id}`, data);
        showNotification('Το έργο ενημερώθηκε επιτυχώς');
      } else {
        await api.post('/api/projects/', data);
        showNotification('Το έργο δημιουργήθηκε επιτυχώς');
      }
      
      handleCloseModal();
      loadProjects();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα αποθήκευσης', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/projects/${deleteConfirm.id}`);
      showNotification('Το έργο διαγράφηκε επιτυχώς');
      setDeleteConfirm(null);
      loadProjects();
    } catch (_error) {
      showNotification('Σφάλμα διαγραφής', 'error');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      planning: 'bg-gray-100 text-gray-800',
      active: 'bg-green-100 text-green-800',
      on_hold: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    const labels = {
      planning: 'Προγραμματισμός',
      active: 'Ενεργό',
      on_hold: 'Σε Αναμονή',
      completed: 'Ολοκληρωμένο',
      cancelled: 'Ακυρωμένο',
    };
    return (
      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  if (loading) {
    return <div className="text-center py-12">Φόρτωση...</div>;
  }

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Έργα</h1>
        <button
          onClick={() => handleOpenModal()}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
        >
          + Νέο Έργο
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Κωδικός</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Όνομα</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Πελάτης</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Τοποθεσία</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Κατάσταση</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ενέργειες</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {projects.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                  Δεν υπάρχουν έργα
                </td>
              </tr>
            ) : (
              projects.map((project) => (
                <tr key={project.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{project.code}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{project.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{project.client_name || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{project.location || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{getStatusBadge(project.status)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/projects/${project.id}`}
                      className="text-primary-600 hover:text-primary-900 mr-4"
                    >
                      Λεπτομέρειες
                    </Link>
                    <button
                      onClick={() => handleOpenModal(project)}
                      className="text-primary-600 hover:text-primary-900 mr-4"
                    >
                      Επεξεργασία
                    </button>
                    <button
                      onClick={() => setDeleteConfirm(project)}
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
        title={editingProject ? 'Επεξεργασία Έργου' : 'Νέο Έργο'}
        size="lg"
      >
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-2 gap-4">
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
              <label className="block text-sm font-medium text-gray-700">Τοποθεσία</label>
              <input
                type="text"
                value={formData.location || ''}
                onChange={(e) => setFormData({...formData, location: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Πελάτης</label>
              <input
                type="text"
                value={formData.client_name || ''}
                onChange={(e) => setFormData({...formData, client_name: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Κατάσταση</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({...formData, status: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              >
                <option value="planning">Προγραμματισμός</option>
                <option value="active">Ενεργό</option>
                <option value="on_hold">Σε Αναμονή</option>
                <option value="completed">Ολοκληρωμένο</option>
                <option value="cancelled">Ακυρωμένο</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Προϋπολογισμός (€)</label>
              <input
                type="number"
                step="0.01"
                value={formData.budget || ''}
                onChange={(e) => setFormData({...formData, budget: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Ημ/νία Έναρξης</label>
              <input
                type="date"
                value={formData.start_date || ''}
                onChange={(e) => setFormData({...formData, start_date: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Ημ/νία Λήξης</label>
              <input
                type="date"
                value={formData.end_date || ''}
                onChange={(e) => setFormData({...formData, end_date: e.target.value})}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              {editingProject ? 'Ενημέρωση' : 'Δημιουργία'}
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

      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDelete}
        title="Διαγραφή Έργου"
        message={`Είστε σίγουροι ότι θέλετε να διαγράψετε το έργο "${deleteConfirm?.name}";`}
      />
    </div>
  );
};

export default Projects;
