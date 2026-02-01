import React from 'react';
import Tooltip from './Tooltip';

const FormField = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  error,
  required = false,
  placeholder,
  helpText,
  icon,
  disabled = false,
  className = '',
  ...props
}) => {
  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label htmlFor={name} className="label flex items-center">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
          {helpText && (
            <Tooltip content={helpText} position="right">
              <span className="ml-2 text-gray-400 cursor-help">ⓘ</span>
            </Tooltip>
          )}
        </label>
      )}

      <div className="relative">
        {icon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
            {icon}
          </div>
        )}

        <input
          id={name}
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          className={`input-field ${icon ? 'pl-10' : ''} ${error ? 'border-red-500 focus:ring-red-500' : ''} ${
            disabled ? 'opacity-60 cursor-not-allowed' : ''
          }`}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : undefined}
          {...props}
        />
      </div>

      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm text-red-600 dark:text-red-400 animate-fade-in">
          {error}
        </p>
      )}
    </div>
  );
};

export default FormField;
