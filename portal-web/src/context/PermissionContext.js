import React, { createContext, useContext, useEffect, useState } from 'react';
import api from '../services/api';

const PermissionContext = createContext(null);

export const PermissionProvider = ({ children }) => {
  const [permissions, setPermissions] = useState([]);
  const [userRole, setUserRole] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPermissions();
  }, []);

  const fetchPermissions = async () => {
    try {
      const response = await api.get('/api/users/me/permissions');
      setPermissions(response.data.permissions || []);
      setUserRole(response.data.role || null);
    } catch (error) {
      console.error('Error fetching permissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const hasPermission = (permission) => permissions.includes(permission);

  const hasAnyPermission = (permissionList) =>
    permissionList.some((p) => permissions.includes(p));

  const hasAllPermissions = (permissionList) =>
    permissionList.every((p) => permissions.includes(p));

  const hasRole = (role) => {
    if (Array.isArray(role)) {
      return role.includes(userRole);
    }
    return userRole === role;
  };

  const isAdmin = () => userRole === 'admin';
  const isManager = () => userRole === 'manager' || userRole === 'admin';
  const isSupervisor = () => ['supervisor', 'manager', 'admin'].includes(userRole);

  const value = {
    permissions,
    userRole,
    loading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    isAdmin,
    isManager,
    isSupervisor,
    refreshPermissions: fetchPermissions,
  };

  return (
    <PermissionContext.Provider value={value}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within PermissionProvider');
  }
  return context;
};
