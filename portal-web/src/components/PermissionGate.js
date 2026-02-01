import { usePermissions } from '../context/PermissionContext';

const PermissionGate = ({
  children,
  permission = null,
  role = null,
  requireAll = false,
  fallback = null,
}) => {
  const { hasPermission, hasAllPermissions, hasRole, loading } = usePermissions();

  if (loading) {
    return null;
  }

  if (permission) {
    const allowed = Array.isArray(permission)
      ? requireAll
        ? hasAllPermissions(permission)
        : permission.some((p) => hasPermission(p))
      : hasPermission(permission);

    if (!allowed) {
      return fallback;
    }
  }

  if (role && !hasRole(role)) {
    return fallback;
  }

  return children;
};

export default PermissionGate;
