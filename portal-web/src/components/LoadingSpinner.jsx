import React from 'react';

/**
 * Reusable loading spinner component
 * Supports multiple sizes and display modes
 */
const LoadingSpinner = ({ 
  message = 'Φόρτωση...', 
  fullScreen = false,
  size = 'medium',
  showMessage = true 
}) => {
  // Size variants
  const sizeClasses = {
    small: 'h-6 w-6 border-2',
    medium: 'h-12 w-12 border-2',
    large: 'h-16 w-16 border-4'
  };

  const containerClass = fullScreen 
    ? 'min-h-screen flex items-center justify-center bg-gray-50'
    : 'flex items-center justify-center p-8';

  return (
    <div className={containerClass}>
      <div className="text-center">
        <div 
          className={`inline-block animate-spin rounded-full border-b-primary-600 border-t-transparent ${sizeClasses[size]}`}
        ></div>
        {showMessage && (
          <p className="mt-4 text-gray-600">{message}</p>
        )}
      </div>
    </div>
  );
};

/**
 * Skeleton loader for content areas
 * Use while loading lists, cards, or page content
 */
export const SkeletonLoader = ({ rows = 3, columns = 3 }) => (
  <div className="p-6 animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
    <div className={`grid grid-cols-1 md:grid-cols-${columns} gap-6 mb-6`}>
      {Array.from({ length: columns }).map((_, i) => (
        <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
      ))}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-12 bg-gray-200 rounded-lg mb-4"></div>
    ))}
  </div>
);

/**
 * Table skeleton loader
 * Use while loading data tables
 */
export const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <div className="animate-pulse">
    {/* Header */}
    <div className="flex gap-4 p-4 bg-gray-100 rounded-t-lg">
      {Array.from({ length: columns }).map((_, i) => (
        <div key={i} className="h-4 bg-gray-300 rounded flex-1"></div>
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIdx) => (
      <div key={rowIdx} className="flex gap-4 p-4 border-b border-gray-100">
        {Array.from({ length: columns }).map((_, colIdx) => (
          <div key={colIdx} className="h-4 bg-gray-200 rounded flex-1"></div>
        ))}
      </div>
    ))}
  </div>
);

/**
 * Card skeleton loader
 * Use while loading card components
 */
export const CardSkeleton = () => (
  <div className="bg-white rounded-lg shadow p-6 animate-pulse">
    <div className="h-6 bg-gray-200 rounded w-2/3 mb-4"></div>
    <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
  </div>
);

/**
 * Button loading state
 * Shows spinner inside button while action is processing
 */
export const ButtonSpinner = ({ className = '' }) => (
  <svg 
    className={`animate-spin h-5 w-5 ${className}`} 
    xmlns="http://www.w3.org/2000/svg" 
    fill="none" 
    viewBox="0 0 24 24"
  >
    <circle 
      className="opacity-25" 
      cx="12" 
      cy="12" 
      r="10" 
      stroke="currentColor" 
      strokeWidth="4"
    ></circle>
    <path 
      className="opacity-75" 
      fill="currentColor" 
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    ></path>
  </svg>
);

export default LoadingSpinner;
