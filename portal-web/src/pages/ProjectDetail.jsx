import React, { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import wsService from '../services/websocket';
import { useToast } from '../components/Toast';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const { info } = useToast();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProjectData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(`/api/projects/${projectId}`);
      setProject(response.data);
    } catch (error) {
      console.error('Error loading project:', error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  useEffect(() => {
    const parsedProjectId = parseInt(projectId, 10);
    if (Number.isNaN(parsedProjectId)) {
      return () => {};
    }

    wsService.watchProject(parsedProjectId);

    const handleUpdate = (message) => {
      if (message.project_id === parsedProjectId) {
        info('Το έργο ενημερώθηκε');
        fetchProjectData();
      }
    };

    wsService.on('daily_report_created', handleUpdate);
    wsService.on('issue_created', handleUpdate);

    return () => {
      wsService.unwatchProject(parsedProjectId);
      wsService.off('daily_report_created', handleUpdate);
      wsService.off('issue_created', handleUpdate);
    };
  }, [projectId, fetchProjectData, info]);

  if (loading) {
    return <div className="text-center py-12">Φόρτωση...</div>;
  }

  if (!project) {
    return <div className="text-center py-12">Δεν βρέθηκε έργο</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        <div className="flex items-center gap-4">
          <Link
            to={`/projects/${projectId}/timeline`}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            📅 Timeline
          </Link>
          <Link
            to="/projects"
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            ← Επιστροφή στα έργα
          </Link>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6 space-y-4">
        <div>
          <p className="text-sm text-gray-500">Κωδικός</p>
          <p className="text-lg font-medium text-gray-900">{project.code}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Πελάτης</p>
          <p className="text-lg font-medium text-gray-900">{project.client_name || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Τοποθεσία</p>
          <p className="text-lg font-medium text-gray-900">{project.location || '-'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Κατάσταση</p>
          <p className="text-lg font-medium text-gray-900">{project.status}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Περιγραφή</p>
          <p className="text-gray-700">{project.description || '-'}</p>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;