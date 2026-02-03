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
  
  const colorConfig = {
    red: {
      header: 'bg-red-500',
      headerText: 'text-white',
      body: 'bg-gray-50 dark:bg-gray-300',
      border: 'border-gray-200 dark:border-gray-700',
      badge: 'bg-white/90 text-red-600 dark:bg-red-500/20 dark:text-white',
      empty: 'text-gray-400 dark:text-gray-600',
    },
    yellow: {
      header: 'bg-amber-500',
      headerText: 'text-white',
      body: 'bg-gray-50 dark:bg-gray-300',
      border: 'border-gray-200 dark:border-gray-700',
      badge: 'bg-white/90 text-amber-600 dark:bg-amber-500/20 dark:text-white',
      empty: 'text-gray-400 dark:text-gray-600',
    },
    green: {
      header: 'bg-emerald-500',
      headerText: 'text-white',
      body: 'bg-gray-50 dark:bg-gray-300',
      border: 'border-gray-200 dark:border-gray-700',
      badge: 'bg-white/90 text-emerald-600 dark:bg-emerald-500/20 dark:text-white',
      empty: 'text-gray-400 dark:text-gray-600',
    },
  };

  const config = colorConfig[color];

  return (
    <div
      ref={setNodeRef}
      className={`rounded-xl shadow-lg overflow-hidden border ${config.border} transition-all duration-200 ${
        isOver ? 'ring-2 ring-blue-400 ring-offset-2 scale-[1.02]' : ''
      }`}
    >
      {/* Column Header */}
      <div className={`${config.header} px-4 py-3`}>
        <div className="flex items-center justify-between">
          <h3 className={`font-semibold text-lg ${config.headerText}`}>{title}</h3>
          <span className={`text-sm font-bold px-3 py-1 rounded-full ${config.badge}`}>
            {items.length}
          </span>
        </div>
      </div>

      {/* Column Body */}
      <div className={`${config.body} p-4`}>
        <SortableContext items={items.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-3 min-h-[250px]">
            {items.length === 0 ? (
              <div className={`flex flex-col items-center justify-center h-[200px] ${config.empty}`}>
                <svg className="w-12 h-12 mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p className="text-sm font-medium">Κανένα issue</p>
                <p className="text-xs opacity-75">Σύρετε issues εδώ</p>
              </div>
            ) : (
              items.map((item) => (
                <SortableIssueCard key={item.id} issue={item} />
              ))
            )}
          </div>
        </SortableContext>
      </div>
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
    critical: { 
      icon: '🔴', 
      color: 'text-red-700 dark:text-red-300', 
      bg: 'bg-red-100 dark:bg-red-900/50',
      border: 'border-l-red-500',
    },
    high: { 
      icon: '🟠', 
      color: 'text-orange-700 dark:text-orange-300', 
      bg: 'bg-orange-100 dark:bg-orange-900/50',
      border: 'border-l-orange-500',
    },
    medium: { 
      icon: '🟡', 
      color: 'text-yellow-700 dark:text-yellow-300', 
      bg: 'bg-yellow-100 dark:bg-yellow-900/50',
      border: 'border-l-yellow-500',
    },
    low: { 
      icon: '🟢', 
      color: 'text-green-700 dark:text-green-300', 
      bg: 'bg-green-100 dark:bg-green-900/50',
      border: 'border-l-green-500',
    },
  };

  const config = severityConfig[issue.severity] || severityConfig.medium;

  return (
    <div
      className={`
        bg-white dark:bg-gray-700 rounded-lg p-4 
        border-l-4 ${config.border}
        shadow-sm hover:shadow-md 
        cursor-grab active:cursor-grabbing
        transition-all duration-200
        ${isDragging ? 'shadow-xl rotate-2 scale-105' : ''}
        ${issue.severity === 'critical' ? 'ring-2 ring-red-400 ring-opacity-50' : ''}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${config.bg} ${config.color}`}>
          {config.icon} {issue.severity?.toUpperCase()}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">#{issue.id}</span>
      </div>

      {/* Title */}
      <h4 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 leading-tight">
        {issue.title}
      </h4>

      {/* Description */}
      {issue.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {issue.description}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100 dark:border-gray-600">
        <div className="flex items-center gap-2">
          {issue.category && (
            <span className="text-xs bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-2 py-1 rounded capitalize">
              {issue.category}
            </span>
          )}
        </div>
        
        {issue.assigned_to_name && (
          <div className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
            <div className="w-5 h-5 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-300 text-[10px] font-bold">
                {issue.assigned_to_name.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="truncate max-w-[80px]">{issue.assigned_to_name}</span>
          </div>
        )}
      </div>

      {/* Date */}
      <div className="text-[10px] text-gray-400 mt-2 flex items-center gap-1">
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        {new Date(issue.created_at).toLocaleDateString('el-GR')}
      </div>
    </div>
  );
};

export default KanbanBoard;
