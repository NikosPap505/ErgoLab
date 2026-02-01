import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import api from '../services/api';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import { useNotification } from '../components/Notification';

const Documents = () => {
  const [projects, setProjects] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploadModal, setUploadModal] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const { showNotification } = useNotification();
  const navigate = useNavigate();

  const [uploadData, setUploadData] = useState({
    title: '',
    description: '',
    files: [],
  });

  const loadProjects = useCallback(async () => {
    try {
      const response = await api.get('/api/projects/');
      setProjects(response.data);
      if (response.data.length > 0) {
        setSelectedProject(response.data[0].id);
      }
    } catch (_error) {
      showNotification('Σφάλμα φόρτωσης έργων', 'error');
    } finally {
      setLoading(false);
    }
  }, [showNotification]);

  const loadDocuments = useCallback(async () => {
    if (!selectedProject) return;
    try {
      const response = await api.get(`/api/documents/project/${selectedProject}`);
      setDocuments(response.data);
    } catch (_error) {
      // May not have documents yet
      setDocuments([]);
    }
  }, [selectedProject]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (selectedProject) {
      loadDocuments();
    }
  }, [selectedProject, loadDocuments]);

  const onDrop = useCallback((acceptedFiles) => {
    setUploadData(prev => ({ ...prev, files: acceptedFiles }));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    multiple: true,
  });

  const handleUpload = async (e) => {
    e.preventDefault();

    if (uploadData.files.length === 0) {
      showNotification('Παρακαλώ επιλέξτε αρχεία', 'error');
      return;
    }

    try {
      for (const file of uploadData.files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', uploadData.title || file.name);
        formData.append('description', uploadData.description);

        await api.post(`/api/documents/upload/${selectedProject}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      }

      showNotification(`${uploadData.files.length} αρχεία ανέβηκαν επιτυχώς`);
      setUploadModal(false);
      setUploadData({ title: '', description: '', files: [] });
      loadDocuments();
    } catch (error) {
      showNotification(error.response?.data?.detail || 'Σφάλμα μεταφόρτωσης', 'error');
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/api/documents/${deleteConfirm.id}`);
      showNotification('Το έγγραφο διαγράφηκε επιτυχώς');
      setDeleteConfirm(null);
      loadDocuments();
    } catch (_error) {
      showNotification('Σφάλμα διαγραφής', 'error');
    }
  };

  const handleView = (documentId) => {
    navigate(`/documents/${documentId}/annotate`);
  };

  const getFileIcon = (fileType) => {
    const icons = {
      pdf: '📄',
      image: '🖼️',
      photo: '📷',
    };
    return icons[fileType] || '📎';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  if (loading) {
    return <div className="text-center py-12">Φόρτωση...</div>;
  }

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Έγγραφα</h1>
          <p className="mt-2 text-sm text-gray-700">
            Διαχείριση PDFs και Φωτογραφιών με δυνατότητα σχολιασμού
          </p>
        </div>
        <button
          onClick={() => setUploadModal(true)}
          disabled={!selectedProject}
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
        >
          📤 Ανέβασμα Εγγράφων
        </button>
      </div>

      {/* Project Selector */}
      {projects.length > 0 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Έργο</label>
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="block w-full sm:w-96 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.code} - {project.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* No Projects Warning */}
      {projects.length === 0 && (
        <div className="text-center py-12 bg-yellow-50 rounded-lg">
          <span className="text-6xl">⚠️</span>
          <p className="mt-4 text-yellow-700">Δεν υπάρχουν έργα. Δημιουργήστε πρώτα ένα έργο.</p>
          <button
            onClick={() => navigate('/projects')}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            Μετάβαση στα Έργα
          </button>
        </div>
      )}

      {/* Documents Grid */}
      {projects.length > 0 && documents.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <span className="text-6xl">📁</span>
          <p className="mt-4 text-gray-500">Δεν υπάρχουν έγγραφα για αυτό το έργο</p>
          <button
            onClick={() => setUploadModal(true)}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700"
          >
            Ανέβασμα πρώτου εγγράφου
          </button>
        </div>
      )}

      {documents.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white overflow-hidden shadow rounded-lg hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => handleView(doc.id)}
            >
              <div className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-4xl">{getFileIcon(doc.file_type)}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteConfirm(doc);
                    }}
                    className="text-gray-400 hover:text-red-600"
                  >
                    🗑️
                  </button>
                </div>
                <h3 className="text-sm font-medium text-gray-900 truncate" title={doc.title}>
                  {doc.title}
                </h3>
                <p className="mt-1 text-xs text-gray-500">
                  {formatFileSize(doc.file_size)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {new Date(doc.uploaded_at).toLocaleDateString('el-GR')}
                </p>
                <div className="mt-4">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleView(doc.id);
                    }}
                    className="w-full px-3 py-2 border border-primary-300 rounded-md text-sm font-medium text-primary-700 hover:bg-primary-50"
                  >
                    ✏️ Σχολιασμός
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModal}
        onClose={() => {
          setUploadModal(false);
          setUploadData({ title: '', description: '', files: [] });
        }}
        title="Ανέβασμα Εγγράφων"
        size="lg"
      >
        <form onSubmit={handleUpload}>
          <div className="space-y-4">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-300 hover:border-primary-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-6xl mb-4">📤</div>
              {isDragActive ? (
                <p className="text-primary-600 font-medium">Αφήστε τα αρχεία εδώ...</p>
              ) : (
                <div>
                  <p className="text-gray-600 font-medium">
                    Σύρετε αρχεία εδώ ή κλικ για επιλογή
                  </p>
                  <p className="text-sm text-gray-500 mt-2">
                    Υποστηρίζονται: PDF, JPG, PNG, GIF
                  </p>
                </div>
              )}
            </div>

            {/* Selected Files */}
            {uploadData.files.length > 0 && (
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Επιλεγμένα αρχεία ({uploadData.files.length})
                </h4>
                <ul className="space-y-1">
                  {uploadData.files.map((file, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-center">
                      <span className="mr-2">📎</span>
                      {file.name} ({(file.size / 1024).toFixed(2)} KB)
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700">Τίτλος</label>
              <input
                type="text"
                value={uploadData.title}
                onChange={(e) => setUploadData({ ...uploadData, title: e.target.value })}
                placeholder="Προαιρετικό - Θα χρησιμοποιηθεί το όνομα αρχείου"
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Περιγραφή</label>
              <textarea
                rows="3"
                value={uploadData.description}
                onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              />
            </div>
          </div>

          <div className="mt-5 sm:mt-6 sm:flex sm:flex-row-reverse">
            <button
              type="submit"
              disabled={uploadData.files.length === 0}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              Ανέβασμα
            </button>
            <button
              type="button"
              onClick={() => {
                setUploadModal(false);
                setUploadData({ title: '', description: '', files: [] });
              }}
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
        title="Διαγραφή Εγγράφου"
        message={`Είστε σίγουροι ότι θέλετε να διαγράψετε το έγγραφο "${deleteConfirm?.title}";`}
      />
    </div>
  );
};

export default Documents;
