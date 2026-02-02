import React, { useEffect, useState } from 'react';
import KanbanBoard from '../components/KanbanBoard';
import { usePermissions } from '../context/PermissionContext';
import api from '../services/api';

const IssuesKanban = () => {
  const { hasPermission } = usePermissions();
  const [selectedProject, setSelectedProject] = useState(null);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await api.get('/api/projects/');
        setProjects(response.data || []);
      } catch (error) {
        console.error(error);
        setProjects([]);
      }
    };

    loadProjects();
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            📋 Πίνακας Προβλημάτων
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Διαχειριστείτε issues με drag & drop
          </p>
        </div>

        {hasPermission('issue:create') && (
          <button className="btn-primary">
            ➕ Νέο Πρόβλημα
          </button>
        )}
      </div>

      <div className="card mb-6 p-4">
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium">Έργο:</label>
          <select
            value={selectedProject || ''}
            onChange={(e) => setSelectedProject(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="input-field max-w-xs"
          >
            <option value="">Όλα τα έργα</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <KanbanBoard projectId={selectedProject} />
    </div>
  );
};

export default IssuesKanban;
