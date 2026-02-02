import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import wsService from '../services/websocket';
import { useToast } from '../components/Toast';

const Dashboard = () => {
  const { t } = useTranslation();
  const { success, warning, error: showError } = useToast();
  const [stats, setStats] = useState({
    projects: 0,
    materials: 0,
    warehouses: 0,
    transfers: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentActivities, setRecentActivities] = useState([]);

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    const handleDailyReport = (message) => {
      success(`📊 Νέα ημερήσια αναφορά από ${message.created_by}`);

      setRecentActivities((prev) => [
        {
          id: Date.now(),
          type: 'daily_report',
          message: `${message.created_by} δημιούργησε αναφορά για ${message.report_date}`,
          timestamp: message.timestamp,
        },
        ...prev.slice(0, 9),
      ]);
    };

    const handleIssueCreated = (message) => {
      const severityIcon = {
        critical: '🔴',
        high: '🟠',
        medium: '🟡',
        low: '🟢',
      };

      warning(`${severityIcon[message.severity] || '🟡'} ${message.title}`);

      setRecentActivities((prev) => [
        {
          id: Date.now(),
          type: 'issue',
          message: `${message.reported_by}: ${message.title}`,
          timestamp: message.timestamp,
          severity: message.severity,
        },
        ...prev.slice(0, 9),
      ]);
    };

    const handleCriticalIssue = (message) => {
      showError(`🚨 ΚΡΙΤΙΚΟ: ${message.title}`, 0);
    };

    const handleIssueStatusChanged = (message) => {
      success(`✓ Issue #${message.issue_id}: ${message.old_status} → ${message.new_status}`);
    };

    wsService.on('daily_report_created', handleDailyReport);
    wsService.on('issue_created', handleIssueCreated);
    wsService.on('critical_issue', handleCriticalIssue);
    wsService.on('issue_status_changed', handleIssueStatusChanged);

    return () => {
      wsService.off('daily_report_created', handleDailyReport);
      wsService.off('issue_created', handleIssueCreated);
      wsService.off('critical_issue', handleCriticalIssue);
      wsService.off('issue_status_changed', handleIssueStatusChanged);
    };
  }, [success, warning, showError]);

  const loadStats = async () => {
    try {
      const [projects, materials, warehouses] = await Promise.all([
        api.get('/api/projects/'),
        api.get('/api/materials/'),
        api.get('/api/warehouses/'),
      ]);

      setStats({
        projects: projects.data.length,
        materials: materials.data.length,
        warehouses: warehouses.data.length,
        transfers: 0,
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { name: t('dashboard.stats.activeProjects'), value: stats.projects, icon: '🏗️', color: 'bg-blue-500' },
    { name: t('dashboard.stats.totalMaterials'), value: stats.materials, icon: '📦', color: 'bg-green-500' },
    { name: t('dashboard.stats.totalWarehouses'), value: stats.warehouses, icon: '🏭', color: 'bg-purple-500' },
    { name: t('dashboard.stats.totalTransfers'), value: stats.transfers, icon: '🚚', color: 'bg-orange-500' },
  ];

  if (loading) {
    return <div className="text-center py-12">{t('common.loading')}</div>;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">{t('dashboard.title')}</h1>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div key={stat.name} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${stat.color} rounded-md p-3`}>
                  <span className="text-3xl">{stat.icon}</span>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {stat.name}
                    </dt>
                    <dd className="text-3xl font-semibold text-gray-900">
                      {stat.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">{t('dashboard.recentActivity')}</h2>
        {recentActivities.length === 0 ? (
          <p className="text-gray-500">{t('dashboard.noRecentActivity')}</p>
        ) : (
          <ul className="space-y-2">
            {recentActivities.map((activity) => (
              <li
                key={activity.id}
                className={`flex items-center p-3 rounded-lg ${
                  activity.severity === 'critical'
                    ? 'bg-red-50 dark:bg-red-900'
                    : 'bg-gray-50 dark:bg-gray-800'
                }`}
              >
                <span className="flex-1">{activity.message}</span>
                <span className="text-sm text-gray-500">
                  {new Date(activity.timestamp).toLocaleTimeString('el-GR')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
