import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext();

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 3000) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type, duration }]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const success = useCallback((message, duration) => addToast(message, 'success', duration), [addToast]);
  const error = useCallback((message, duration) => addToast(message, 'error', duration), [addToast]);
  const warning = useCallback((message, duration) => addToast(message, 'warning', duration), [addToast]);
  const info = useCallback((message, duration) => addToast(message, 'info', duration), [addToast]);

  return (
    <ToastContext.Provider value={{ success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

const ToastContainer = ({ toasts, removeToast }) => {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {toasts.map(toast => (
        <Toast key={toast.id} {...toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

const Toast = ({ message, type, onClose }) => {
  const typeConfig = {
    success: {
      bg: 'bg-green-50 dark:bg-green-900',
      border: 'border-green-400',
      text: 'text-green-800 dark:text-green-200',
      icon: '✓'
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-900',
      border: 'border-red-400',
      text: 'text-red-800 dark:text-red-200',
      icon: '✗'
    },
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-900',
      border: 'border-yellow-400',
      text: 'text-yellow-800 dark:text-yellow-200',
      icon: '⚠'
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900',
      border: 'border-blue-400',
      text: 'text-blue-800 dark:text-blue-200',
      icon: 'ℹ'
    }
  };

  const config = typeConfig[type] || typeConfig.info;

  return (
    <div
      className={`${config.bg} ${config.text} border-l-4 ${config.border} p-4 rounded-md shadow-lg animate-slide-in-right`}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0 text-xl mr-3">{config.icon}</div>
        <div className="flex-1">
          <p className="text-sm font-medium">{message}</p>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 ml-3 text-lg hover:opacity-75"
        >
          ×
        </button>
      </div>
    </div>
  );
};
