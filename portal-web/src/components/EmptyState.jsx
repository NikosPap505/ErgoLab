import React from 'react';
import { useTranslation } from 'react-i18next';

const EmptyState = ({
  icon = '📭',
  title,
  description,
  actionLabel,
  onAction,
  className = ''
}) => {
  const { t } = useTranslation();

  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="text-6xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        {title || t('emptyState.noData')}
      </h3>
      {description && (
        <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <button onClick={onAction} className="btn-primary">
          {actionLabel}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
