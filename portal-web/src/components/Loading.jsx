import React from 'react';
import { useTranslation } from 'react-i18next';

export const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <div className="animate-spin rounded-full h-full w-full border-b-2 border-indigo-600 dark:border-indigo-400" />
    </div>
  );
};

export const LoadingDots = ({ className = '' }) => {
  return (
    <div className={`flex space-x-1 ${className}`}>
      <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full loading-dot" />
      <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full loading-dot" />
      <div className="w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full loading-dot" />
    </div>
  );
};

export const LoadingOverlay = ({ message }) => {
  const { t } = useTranslation();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-900 dark:text-white font-medium">
          {message || t('common.loading')}
        </p>
      </div>
    </div>
  );
};

export const LoadingPage = () => {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <LoadingSpinner size="xl" className="mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400">{t('common.loading')}</p>
      </div>
    </div>
  );
};
