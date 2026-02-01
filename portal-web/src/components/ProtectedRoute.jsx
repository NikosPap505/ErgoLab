import React from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { usePermissions } from '../context/PermissionContext';

const ProtectedRoute = ({ children, permission = null, role = null, requireAll = false }) => {
  const { user, loading: authLoading } = useAuth();
  const { hasPermission, hasRole, hasAllPermissions, loading: permissionsLoading } = usePermissions();
  const { t } = useTranslation();

  if (authLoading || permissionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">{t('common.loading')}</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (permission) {
    const permitted = Array.isArray(permission)
      ? requireAll
        ? hasAllPermissions(permission)
        : permission.some((p) => hasPermission(p))
      : hasPermission(permission);

    if (!permitted) {
      return <AccessDenied />;
    }
  }

  if (role && !hasRole(role)) {
    return <AccessDenied />;
  }

  return children;
};

const AccessDenied = () => {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="text-6xl mb-4">🔒</div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          {t('errors.accessDenied')}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          {t('errors.noPermission')}
        </p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          {t('common.backToDashboard')}
        </a>
      </div>
    </div>
  );
};

export default ProtectedRoute;
