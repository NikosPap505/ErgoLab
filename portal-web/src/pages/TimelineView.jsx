import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import ProjectTimeline from '../components/Timeline';
import api from '../services/api';

const TimelineView = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await api.get(`/api/projects/${projectId}`);
        setProject(response.data);
      } catch (err) {
        console.error(err);
        setProject(null);
      }
    };

    fetchProject();
  }, [projectId]);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">
          📅 {project?.name || 'Project'} Timeline
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Drag & drop για αναπρογραμματισμό εργασιών
        </p>
      </div>

      <ProjectTimeline projectId={projectId} />
    </div>
  );
};

export default TimelineView;
