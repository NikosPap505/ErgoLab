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
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <span className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-2 rounded-xl shadow-lg">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
            </span>
            Πίνακας Προβλημάτων
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-2 ml-14">
            Διαχειριστείτε issues με drag & drop
          </p>
        </div>

        {hasPermission('issue:create') && (
          <button className="btn-primary flex items-center gap-2 shadow-lg hover:shadow-xl transition-shadow">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Νέο Πρόβλημα
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Έργο:
            </label>
            <div className="relative">
              <select
                value={selectedProject || ''}
                onChange={(e) => setSelectedProject(e.target.value ? parseInt(e.target.value, 10) : null)}
                className="appearance-none bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-10 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all min-w-[200px]"
              >
                <option value="">Όλα τα έργα</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Stats summary */}
          <div className="flex items-center gap-4 ml-auto text-sm">
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <span className="w-3 h-3 bg-red-500 rounded-full"></span>
              <span>Ανοιχτά</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <span className="w-3 h-3 bg-amber-500 rounded-full"></span>
              <span>Σε εξέλιξη</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
              <span className="w-3 h-3 bg-emerald-500 rounded-full"></span>
              <span>Επιλυμένα</span>
            </div>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <KanbanBoard projectId={selectedProject} />
    </div>
  );
};

export default IssuesKanban;
