import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useDroppable } from '@dnd-kit/core';
import api from '../services/api';
import wsService from '../services/websocket';
import { useToast } from './Toast';

const KanbanBoard = ({ projectId }) => {
  const [columns, setColumns] = useState({
    open: { title: 'Ανοιχτά', items: [], color: 'red' },
    in_progress: { title: 'Σε Εξέλιξη', items: [], color: 'yellow' },
    resolved: { title: 'Επιλυμένα', items: [], color: 'green' },
  });
  const [activeId, setActiveId] = useState(null);
  const [loading, setLoading] = useState(true);
  const { success, error } = useToast();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const fetchKanbanData = useCallback(async () => {
    try {
      const params = projectId ? { project_id: projectId } : {};
      const response = await api.get('/api/reports/issues/kanban', { params });
      setColumns((prev) => ({
        open: { ...prev.open, items: response.data.open || [] },
        in_progress: { ...prev.in_progress, items: response.data.in_progress || [] },
        resolved: { ...prev.resolved, items: response.data.resolved || [] },
      }));
    } catch (err) {
      console.error(err);
      error('Σφάλμα φόρτωσης issues');
    } finally {
      setLoading(false);
    }
  }, [projectId, error]);

  useEffect(() => {
    fetchKanbanData();

    const handleIssueMoved = (message) => {
      if (!projectId || message.project_id === projectId) {
        success(`${message.moved_by} μετακίνησε issue`);
        fetchKanbanData();
      }
    };

    const handleIssueChanged = (message) => {
      if (!projectId || message.project_id === projectId) {
        fetchKanbanData();
      }
    };

    wsService.on('issue_moved', handleIssueMoved);
    wsService.on('issue_created', handleIssueChanged);
    wsService.on('issue_assignment_changed', handleIssueChanged);

    return () => {
      wsService.off('issue_moved', handleIssueMoved);
      wsService.off('issue_created', handleIssueChanged);
      wsService.off('issue_assignment_changed', handleIssueChanged);
    };
  }, [projectId, success, fetchKanbanData]);

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const findColumn = (id) => {
    for (const [columnId, column] of Object.entries(columns)) {
      if (column.items.find((item) => item.id === id)) {
        return columnId;
      }
    }
    return null;
  };

  const handleDragOver = (event) => {
    const { active, over } = event;
    if (!over) return;

    const activeColumn = findColumn(active.id);
    const overColumn = over.data.current?.sortable?.containerId || over.id;

    if (!activeColumn || !overColumn || activeColumn === overColumn) return;

    setColumns((prev) => {
      const activeItems = [...prev[activeColumn].items];
      const overItems = [...prev[overColumn].items];
      const activeIndex = activeItems.findIndex((item) => item.id === active.id);
      const overIndex = over.data.current?.sortable?.index ?? overItems.length;

      const [movedItem] = activeItems.splice(activeIndex, 1);

      return {
        ...prev,
        [activeColumn]: { ...prev[activeColumn], items: activeItems },
        [overColumn]: {
          ...prev[overColumn],
          items: [...overItems.slice(0, overIndex), movedItem, ...overItems.slice(overIndex)],
        },
      };
    });
  };

  const handleDragEnd = async (event) => {
    const { active, over } = event;

    if (!over) {
      setActiveId(null);
      return;
    }

    const activeColumn = findColumn(active.id);
    const overColumn = over.data.current?.sortable?.containerId || over.id;

    if (!activeColumn || !overColumn) {
      setActiveId(null);
      return;
    }

    if (activeColumn === overColumn) {
      const currentItems = columns[activeColumn].items;
      const oldIndex = currentItems.findIndex((item) => item.id === active.id);
      const newIndex = over.data.current?.sortable?.index ?? oldIndex;

      if (oldIndex !== newIndex) {
        setColumns((prev) => ({
          ...prev,
          [activeColumn]: {
            ...prev[activeColumn],
            items: arrayMove(prev[activeColumn].items, oldIndex, newIndex),
          },
        }));
      }
      setActiveId(null);
      return;
    }

    try {
      await api.put(`/api/reports/issues/${active.id}/move`, {
        status: overColumn,
        position: 0,
      });
      success('Issue ενημερώθηκε');
    } catch (err) {
      console.error(err);
      error('Σφάλμα ενημέρωσης issue');
      fetchKanbanData();
    }

    setActiveId(null);
  };

  const activeItem = useMemo(() => {
    if (!activeId) return null;
    return Object.values(columns)
      .flatMap((col) => col.items)
      .find((item) => item.id === activeId);
  }, [activeId, columns]);

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.entries(columns).map(([columnId, column]) => (
          <KanbanColumn
            key={columnId}
            id={columnId}
            title={column.title}
            color={column.color}
            items={column.items}
          />
        ))}
      </div>

      <DragOverlay>{activeItem ? <IssueCard issue={activeItem} isDragging /> : null}</DragOverlay>
    </DndContext>
  );
};

const KanbanColumn = ({ id, title, color, items }) => {
  const { isOver, setNodeRef } = useDroppable({ id });
  const colorClasses = {
    red: 'bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700',
    yellow: 'bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700',
    green: 'bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700',
  };

  return (
    <div
      ref={setNodeRef}
      className={`rounded-lg border-2 ${colorClasses[color]} p-4 ${isOver ? 'drop-zone-active' : ''}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-lg">{title}</h3>
        <span className="text-sm text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-800 px-2 py-1 rounded-full">
          {items.length}
        </span>
      </div>

      <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-3 min-h-[200px]">
          {items.map((item) => (
            <SortableIssueCard key={item.id} issue={item} />
          ))}
        </div>
      </SortableContext>
    </div>
  );
};

const SortableIssueCard = ({ issue }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: issue.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <IssueCard issue={issue} />
    </div>
  );
};

const IssueCard = ({ issue, isDragging = false }) => {
  const severityConfig = {
    critical: { icon: '🔴', color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900' },
    high: { icon: '🟠', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900' },
    medium: { icon: '🟡', color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-100 dark:bg-yellow-900' },
    low: { icon: '🟢', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900' },
  };

  const config = severityConfig[issue.severity] || severityConfig.medium;

  return (
    <div
      className={`card p-4 cursor-move hover:shadow-lg transition-shadow ${
        isDragging ? 'dragging' : ''
      } ${issue.severity === 'critical' ? 'border-2 border-red-500 animate-pulse-border' : ''}`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className={`text-xs font-semibold px-2 py-1 rounded ${config.bg} ${config.color}`}>
          {config.icon} {issue.severity.toUpperCase()}
        </span>
        <span className="text-xs text-gray-500">#{issue.id}</span>
      </div>

      <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{issue.title}</h4>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
        {issue.description}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="capitalize">{issue.category}</span>
        {issue.assigned_to_name && (
          <div className="flex items-center">
            <span className="mr-1">👤</span>
            <span>{issue.assigned_to_name}</span>
          </div>
        )}
      </div>

      <div className="text-xs text-gray-400 mt-2">
        {new Date(issue.created_at).toLocaleDateString('el-GR')}
      </div>
    </div>
  );
};

export default KanbanBoard;
