import React from 'react';
import { useTranslation } from 'react-i18next';

const ROLE_STYLES = {
  admin: 'bg-red-100 text-red-800',
  manager: 'bg-purple-100 text-purple-800',
  supervisor: 'bg-blue-100 text-blue-800',
  worker: 'bg-green-100 text-green-800',
  viewer: 'bg-gray-100 text-gray-800',
};

const normalizeRole = (role) => {
  if (!role) return '';
  if (typeof role === 'string') return role.toLowerCase();
  if (role.value) return String(role.value).toLowerCase();
  return String(role).toLowerCase();
};

const RoleBadge = ({ role }) => {
  const { t } = useTranslation();
  const roleKey = normalizeRole(role);
  const style = ROLE_STYLES[roleKey] || 'bg-gray-100 text-gray-800';

  return (
    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${style}`}>
      {t(`roles.${roleKey}`, roleKey || '-')}
    </span>
  );
};

export default RoleBadge;
