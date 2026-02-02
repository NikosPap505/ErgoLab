import React, { useCallback, useEffect, useState } from 'react';
import Timeline from 'react-calendar-timeline';
import 'react-calendar-timeline/lib/Timeline.css';
import moment from 'moment';
import api from '../services/api';
import { useToast } from './Toast';

const ProjectTimeline = ({ projectId }) => {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const { success, error } = useToast();

  const fetchTimelineData = useCallback(async () => {
    try {
      const response = await api.get(`/api/projects/${projectId}/timeline`);
      setTimelineData(response.data);
    } catch (err) {
      console.error(err);
      error('Σφάλμα φόρτωσης timeline');
    } finally {
      setLoading(false);
    }
  }, [projectId, error]);

  useEffect(() => {
    fetchTimelineData();
  }, [projectId, fetchTimelineData]);

  if (loading) {
    return <div className="text-center py-12">Loading timeline...</div>;
  }

  if (!timelineData || timelineData.work_items.length === 0) {
    return (
      <div className="card p-6 text-center">
        <p className="text-gray-600 dark:text-gray-400">
          Δεν υπάρχουν εργασίες για αυτό το έργο.
        </p>
      </div>
    );
  }

  const groups = [
    { id: 0, title: 'Unassigned' },
    ...timelineData.workers.map((worker) => ({
      id: worker.id,
      title: worker.name,
    })),
  ];

  const items = timelineData.work_items.map((item) => {
    const groupId = item.assigned_to || 0;
    const statusColors = {
      planned: '#94a3b8',
      in_progress: '#3b82f6',
      completed: '#10b981',
      delayed: '#ef4444',
      blocked: '#f59e0b',
    };

    const isCritical = timelineData.critical_path.includes(item.id);
    const bgColor = isCritical ? '#dc2626' : statusColors[item.status];

    return {
      id: item.id,
      group: groupId,
      title: item.name,
      start_time: moment(item.planned_start).valueOf(),
      end_time: moment(item.planned_end).valueOf(),
      canMove: true,
      canResize: true,
      canChangeGroup: true,
      itemProps: {
        style: {
          background: bgColor,
          color: 'white',
          border: isCritical ? '3px solid #991b1b' : 'none',
          borderRadius: '4px',
          boxShadow: isCritical ? '0 4px 6px rgba(220, 38, 38, 0.5)' : 'none',
        },
      },
      status: item.status,
      progress: item.progress_percentage,
      isDelayed: item.is_delayed,
      isCritical,
      dependsOn: item.depends_on_id,
    };
  });

  const handleItemMove = async (itemId, dragTime, newGroupOrder) => {
    const newGroup = groups[newGroupOrder].id;
    const newStart = moment(dragTime);
    const item = items.find((i) => i.id === itemId);
    const duration = moment(item.end_time).diff(moment(item.start_time), 'days');
    const newEnd = newStart.clone().add(duration, 'days');

    try {
      await api.put(`/api/projects/work-items/${itemId}`, {
        planned_start: newStart.format('YYYY-MM-DD'),
        planned_end: newEnd.format('YYYY-MM-DD'),
        assigned_to: newGroup === 0 ? null : newGroup,
      });
      fetchTimelineData();
    } catch (err) {
      console.error(err);
      error('Σφάλμα ενημέρωσης εργασίας');
      fetchTimelineData();
    }
  };

  const handleItemResize = async (itemId, time, edge) => {
    const item = items.find((i) => i.id === itemId);
    let newStart = moment(item.start_time);
    let newEnd = moment(item.end_time);

    if (edge === 'left') {
      newStart = moment(time);
    } else {
      newEnd = moment(time);
    }

    try {
      await api.put(`/api/projects/work-items/${itemId}`, {
        planned_start: newStart.format('YYYY-MM-DD'),
        planned_end: newEnd.format('YYYY-MM-DD'),
      });
      fetchTimelineData();
    } catch (err) {
      console.error(err);
      error('Σφάλμα ενημέρωσης διάρκειας');
      fetchTimelineData();
    }
  };

  const handleItemClick = (itemId) => {
    const item = timelineData.work_items.find((i) => i.id === itemId);
    if (item) {
      setSelectedItem({
        ...item,
        is_critical: timelineData.critical_path.includes(item.id),
      });
      setShowDetailModal(true);
    }
  };

  return (
    <div>
      <div className="card p-4 mb-4">
        <div className="flex flex-wrap gap-4 items-center">
          <span className="text-sm font-semibold">Κατάσταση:</span>
          <div className="flex items-center">
            <span className="w-4 h-4 bg-gray-400 rounded mr-2"></span>
            <span className="text-sm">Planned</span>
          </div>
          <div className="flex items-center">
            <span className="w-4 h-4 bg-blue-500 rounded mr-2"></span>
            <span className="text-sm">In Progress</span>
          </div>
          <div className="flex items-center">
            <span className="w-4 h-4 bg-green-500 rounded mr-2"></span>
            <span className="text-sm">Completed</span>
          </div>
          <div className="flex items-center">
            <span className="w-4 h-4 bg-red-500 rounded mr-2"></span>
            <span className="text-sm">Delayed</span>
          </div>
          <div className="flex items-center">
            <span className="w-4 h-4 bg-orange-500 rounded mr-2"></span>
            <span className="text-sm">Blocked</span>
          </div>
          <div className="flex items-center border-2 border-red-900 px-2 py-1 rounded">
            <span className="w-4 h-4 bg-red-600 rounded mr-2"></span>
            <span className="text-sm font-bold">Critical Path</span>
          </div>
        </div>
      </div>

      <div className="card p-4">
        <Timeline
          groups={groups}
          items={items}
          defaultTimeStart={moment(timelineData.start_date).subtract(7, 'days')}
          defaultTimeEnd={moment(timelineData.end_date).add(7, 'days')}
          onItemMove={handleItemMove}
          onItemResize={handleItemResize}
          onItemClick={handleItemClick}
          canMove
          canResize="both"
          canChangeGroup
          lineHeight={50}
          itemHeightRatio={0.75}
          stackItems
          buffer={3}
          minZoom={1000 * 60 * 60 * 24}
          maxZoom={1000 * 60 * 60 * 24 * 365}
        />
      </div>

      {showDetailModal && selectedItem && (
        <WorkItemDetailModal
          item={selectedItem}
          onClose={() => setShowDetailModal(false)}
          onUpdate={fetchTimelineData}
          onSuccess={success}
          onError={error}
        />
      )}
    </div>
  );
};

const WorkItemDetailModal = ({ item, onClose, onUpdate, onSuccess, onError }) => {
  const [progress, setProgress] = useState(item.progress_percentage);
  const [status, setStatus] = useState(item.status);

  const handleUpdate = async () => {
    try {
      await api.put(`/api/projects/work-items/${item.id}`, {
        progress_percentage: progress,
        status: status,
      });
      onSuccess('Εργασία ενημερώθηκε');
      onUpdate();
      onClose();
    } catch (err) {
      console.error(err);
      onError('Σφάλμα ενημέρωσης');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-2xl font-bold">{item.name}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>

        {item.is_critical && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
            <div className="flex items-center">
              <span className="text-red-700 font-semibold">
                ⚠️ Αυτή η εργασία είναι στο Critical Path!
              </span>
            </div>
            <p className="text-sm text-red-600 mt-1">
              Καθυστέρηση σε αυτή την εργασία θα καθυστερήσει ολόκληρο το έργο.
            </p>
          </div>
        )}

        {item.is_delayed && (
          <div className="bg-orange-50 border-l-4 border-orange-500 p-4 mb-4">
            <span className="text-orange-700 font-semibold">⏰ Καθυστερημένη εργασία</span>
          </div>
        )}

        <div className="space-y-4">
          {item.description && (
            <div>
              <label className="label">Περιγραφή</label>
              <p className="text-gray-700 dark:text-gray-300">{item.description}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Προγραμματισμένη Έναρξη</label>
              <p className="font-semibold">{moment(item.planned_start).format('DD/MM/YYYY')}</p>
            </div>
            <div>
              <label className="label">Προγραμματισμένη Λήξη</label>
              <p className="font-semibold">{moment(item.planned_end).format('DD/MM/YYYY')}</p>
            </div>
          </div>

          <div>
            <label className="label">Πρόοδος: {progress}%</label>
            <input
              type="range"
              min="0"
              max="100"
              value={progress}
              onChange={(e) => setProgress(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="label">Κατάσταση</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input-field"
            >
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="delayed">Delayed</option>
              <option value="blocked">Blocked</option>
            </select>
          </div>

          {item.assigned_user_name && (
            <div>
              <label className="label">Ανατέθηκε σε</label>
              <p className="font-semibold">{item.assigned_user_name}</p>
            </div>
          )}

          {item.depends_on_name && (
            <div>
              <label className="label">Εξαρτάται από</label>
              <p className="font-semibold">{item.depends_on_name}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Εκτιμώμενες Ώρες</label>
              <p>{item.estimated_hours || '-'}</p>
            </div>
            <div>
              <label className="label">Πραγματικές Ώρες</label>
              <p>{item.actual_hours || '-'}</p>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary flex-1">
            Κλείσιμο
          </button>
          <button onClick={handleUpdate} className="btn-primary flex-1">
            Αποθήκευση
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProjectTimeline;
