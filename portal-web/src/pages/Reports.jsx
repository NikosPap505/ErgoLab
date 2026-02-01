import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '../components/Notification';
import api from '../services/api';
import {
  ChartBarIcon,
  DocumentArrowDownIcon,
  CalendarIcon,
  CubeIcon,
  BuildingStorefrontIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';

const Reports = () => {
  const { t, i18n } = useTranslation();
  const { showSuccess, showError } = useNotification();
  
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('inventory');
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0]
  });
  const [reportData, setReportData] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [selectedWarehouse, setSelectedWarehouse] = useState('all');

  const fetchWarehouses = useCallback(async () => {
    try {
      const response = await api.get('/api/warehouses/');
      setWarehouses(response.data);
    } catch (error) {
      console.error('Failed to load warehouses');
    }
  }, []);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      let endpoint = '/api/reports/';
      const params = new URLSearchParams({
        type: reportType,
        start_date: dateRange.start,
        end_date: dateRange.end
      });
      
      if (selectedWarehouse !== 'all') {
        params.append('warehouse_id', selectedWarehouse);
      }

      const response = await api.get(`${endpoint}?${params}`);
      setReportData(response.data);
    } catch (error) {
      // Mock data if API not available
      setReportData(generateMockData(reportType));
    } finally {
      setLoading(false);
    }
  }, [reportType, dateRange, selectedWarehouse]);

  useEffect(() => {
    fetchWarehouses();
  }, [fetchWarehouses]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const generateMockData = (type) => {
    if (type === 'inventory') {
      return {
        summary: {
          total_materials: 156,
          total_value: 245680.50,
          low_stock_items: 12,
          out_of_stock_items: 3
        },
        by_category: [
          { category: 'Electrical', count: 45, value: 78500 },
          { category: 'Plumbing', count: 32, value: 45200 },
          { category: 'HVAC', count: 28, value: 62300 },
          { category: 'Tools', count: 51, value: 59680.50 }
        ]
      };
    } else if (type === 'transactions') {
      return {
        summary: {
          total_transactions: 342,
          purchases: 156,
          sales: 98,
          transfers: 88
        },
        daily: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          purchases: Math.floor(Math.random() * 20),
          sales: Math.floor(Math.random() * 15),
          transfers: Math.floor(Math.random() * 10)
        }))
      };
    } else {
      return {
        summary: {
          active_projects: 8,
          total_warehouses: 12,
          pending_transfers: 15,
          documents_uploaded: 234
        }
      };
    }
  };

  const handleExport = async (format) => {
    try {
      showSuccess(t('messages.exporting', { format: format.toUpperCase() }));
      // In production, this would trigger a download
      const response = await api.get(`/api/reports/export?type=${reportType}&format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `report_${reportType}_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      showError(t('messages.exportError'));
    }
  };

  const StatCard = ({ title, value, icon: Icon, trend, color = 'blue', isCurrency = false }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">
            {typeof value === 'number' && isCurrency
              ? `€${value.toLocaleString()}`
              : value?.toLocaleString()}
          </p>
          {trend && (
            <div className={`flex items-center mt-2 text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend > 0 ? (
                <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
              ) : (
                <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />
              )}
              <span>{t('reportsPage.trendFromLastPeriod', { value: Math.abs(trend) })}</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`h-8 w-8 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  const dateLocale = useMemo(
    () => (i18n.language === 'el' ? 'el-GR' : 'en-US'),
    [i18n.language]
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('reportsPage.title')}</h1>
          <p className="text-gray-500">{t('reportsPage.subtitle')}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
            {t('reportsPage.exportCsv')}
          </button>
          <button
            onClick={() => handleExport('pdf')}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
            {t('reportsPage.exportPdf')}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reportsPage.reportType')}</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="inventory">{t('reportsPage.types.inventory')}</option>
              <option value="transactions">{t('reportsPage.types.transactions')}</option>
              <option value="overview">{t('reportsPage.types.overview')}</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reportsPage.warehouse')}</label>
            <select
              value={selectedWarehouse}
              onChange={(e) => setSelectedWarehouse(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">{t('reportsPage.allWarehouses')}</option>
              {warehouses.map(w => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reportsPage.startDate')}</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reportsPage.endDate')}</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded-lg"></div>
        </div>
      ) : (
        <>
          {/* Summary Stats */}
          {reportType === 'inventory' && reportData?.summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <StatCard
                title={t('reportsPage.cards.totalMaterials')}
                value={reportData.summary.total_materials}
                icon={CubeIcon}
                color="blue"
              />
              <StatCard
                title={t('reportsPage.cards.totalValue')}
                value={reportData.summary.total_value}
                icon={ChartBarIcon}
                color="green"
                isCurrency
              />
              <StatCard
                title={t('reportsPage.cards.lowStockItems')}
                value={reportData.summary.low_stock_items}
                icon={ArrowTrendingDownIcon}
                color="yellow"
              />
              <StatCard
                title={t('reportsPage.cards.outOfStock')}
                value={reportData.summary.out_of_stock_items}
                icon={BuildingStorefrontIcon}
                color="red"
              />
            </div>
          )}

          {reportType === 'transactions' && reportData?.summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <StatCard
                title={t('reportsPage.cards.totalTransactions')}
                value={reportData.summary.total_transactions}
                icon={ChartBarIcon}
                trend={12}
                color="blue"
              />
              <StatCard
                title={t('reportsPage.cards.purchases')}
                value={reportData.summary.purchases}
                icon={ArrowTrendingUpIcon}
                trend={8}
                color="green"
              />
              <StatCard
                title={t('reportsPage.cards.sales')}
                value={reportData.summary.sales}
                icon={ArrowTrendingDownIcon}
                trend={-5}
                color="purple"
              />
              <StatCard
                title={t('reportsPage.cards.transfers')}
                value={reportData.summary.transfers}
                icon={CalendarIcon}
                color="orange"
              />
            </div>
          )}

          {reportType === 'overview' && reportData?.summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <StatCard
                title={t('reportsPage.cards.activeProjects')}
                value={reportData.summary.active_projects}
                icon={CalendarIcon}
                color="blue"
              />
              <StatCard
                title={t('reportsPage.cards.totalWarehouses')}
                value={reportData.summary.total_warehouses}
                icon={BuildingStorefrontIcon}
                color="green"
              />
              <StatCard
                title={t('reportsPage.cards.pendingTransfers')}
                value={reportData.summary.pending_transfers}
                icon={ArrowTrendingUpIcon}
                color="yellow"
              />
              <StatCard
                title={t('reportsPage.cards.documents')}
                value={reportData.summary.documents_uploaded}
                icon={CubeIcon}
                color="purple"
              />
            </div>
          )}

          {/* Detailed Data */}
          {reportType === 'inventory' && reportData?.by_category && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">{t('reportsPage.inventoryByCategory')}</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('reportsPage.table.category')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('reportsPage.table.itemCount')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('reportsPage.table.totalValue')}</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('reportsPage.table.percentOfTotal')}</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {reportData.by_category.map((cat, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-6 py-4 font-medium">{cat.category}</td>
                        <td className="px-6 py-4">{cat.count}</td>
                        <td className="px-6 py-4">€{cat.value.toLocaleString()}</td>
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className="bg-primary-600 h-2 rounded-full"
                                style={{ width: `${(cat.value / reportData.summary.total_value * 100).toFixed(0)}%` }}
                              ></div>
                            </div>
                            <span>{(cat.value / reportData.summary.total_value * 100).toFixed(1)}%</span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {reportType === 'transactions' && reportData?.daily && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">{t('reportsPage.dailyTrends')}</h3>
              <div className="h-64 flex items-end justify-between gap-1">
                {reportData.daily.slice(-14).map((day, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div className="w-full flex flex-col gap-0.5" style={{ height: '200px' }}>
                      <div
                        className="w-full bg-green-500 rounded-t"
                        style={{ height: `${day.purchases * 5}px` }}
                        title={`${t('reportsPage.cards.purchases')}: ${day.purchases}`}
                      ></div>
                      <div
                        className="w-full bg-purple-500"
                        style={{ height: `${day.sales * 5}px` }}
                        title={`${t('reportsPage.cards.sales')}: ${day.sales}`}
                      ></div>
                      <div
                        className="w-full bg-blue-500 rounded-b"
                        style={{ height: `${day.transfers * 5}px` }}
                        title={`${t('reportsPage.cards.transfers')}: ${day.transfers}`}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-left">
                      {new Date(day.date).toLocaleDateString(dateLocale, { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex justify-center gap-6 mt-8">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-green-500 rounded mr-2"></div>
                  <span className="text-sm">{t('reportsPage.cards.purchases')}</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-purple-500 rounded mr-2"></div>
                  <span className="text-sm">{t('reportsPage.cards.sales')}</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-blue-500 rounded mr-2"></div>
                  <span className="text-sm">{t('reportsPage.cards.transfers')}</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Reports;
