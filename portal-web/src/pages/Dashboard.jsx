import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../services/api';

const Dashboard = () => {
  const { t } = useTranslation();
  const [stats, setStats] = useState({
    projects: 0,
    materials: 0,
    warehouses: 0,
    transfers: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

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
        <p className="text-gray-500">{t('dashboard.noRecentActivity')}</p>
      </div>
    </div>
  );
};

export default Dashboard;
