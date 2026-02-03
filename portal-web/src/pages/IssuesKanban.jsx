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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Πίνακας Προβλημάτων
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Διαχειριστείτε issues με drag & drop
          </p>
        </div>

        {hasPermission('issue:create') && (
          <button className="flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
            <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Νέο Πρόβλημα
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-lg shadow">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">
            Έργο:
          </label>
          <select
            value={selectedProject || ''}
            onChange={(e) => setSelectedProject(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
          >
            <option value="">Όλα τα έργα</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {/* Stats summary */}
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 text-gray-500">
            <span className="w-2.5 h-2.5 bg-red-500 rounded-full"></span>
            <span>Ανοιχτά</span>
          </div>
          <div className="flex items-center gap-2 text-gray-500">
            <span className="w-2.5 h-2.5 bg-amber-500 rounded-full"></span>
            <span>Σε εξέλιξη</span>
          </div>
          <div className="flex items-center gap-2 text-gray-500">
            <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>
            <span>Επιλυμένα</span>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <KanbanBoard projectId={selectedProject} />
    </div>
  );
};

export default IssuesKanban;
