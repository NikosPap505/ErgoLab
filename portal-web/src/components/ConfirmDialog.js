import React from 'react';
import { useTranslation } from 'react-i18next';

const ConfirmDialog = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText,
  cancelText,
  type = 'danger'
}) => {
  const { t } = useTranslation();

  if (!isOpen) return null;

  const typeConfig = {
    danger: {
      icon: '🗑️',
      confirmClass: 'btn-danger',
      iconBg: 'bg-red-100 dark:bg-red-900'
    },
    warning: {
      icon: '⚠️',
      confirmClass: 'bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md',
      iconBg: 'bg-yellow-100 dark:bg-yellow-900'
    },
    info: {
      icon: 'ℹ️',
      confirmClass: 'btn-primary',
      iconBg: 'bg-blue-100 dark:bg-blue-900'
    }
  };

  const config = typeConfig[type];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 animate-scale-in">
        <div className="flex items-start">
          <div className={`flex-shrink-0 ${config.iconBg} rounded-full p-3 mr-4`}>
            <span className="text-2xl">{config.icon}</span>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {title}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              {message}
            </p>
          </div>
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <button
            onClick={onClose}
            className="btn-secondary"
          >
            {cancelText || t('common.cancel')}
          </button>
          <button
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className={config.confirmClass}
          >
            {confirmText || t('common.confirm')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
