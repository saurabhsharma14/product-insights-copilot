import type { ReactNode, FC } from 'react';
import clsx from 'clsx';

export const Card: FC<{ children: ReactNode, className?: string }> = ({ children, className }) => (
  <div className={clsx("bg-white rounded-xl shadow-sm border border-gray-100 p-6", className)}>
    {children}
  </div>
);

export const Badge: FC<{ children: ReactNode, variant?: 'success' | 'warning' | 'error' | 'neutral' }> = ({ children, variant = 'neutral' }) => {
  const styles = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    neutral: 'bg-gray-100 text-gray-800'
  };
  return (
    <span className={clsx("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", styles[variant])}>
      {children}
    </span>
  );
};

export const StatusIndicator: FC<{ active: boolean, label: string }> = ({ active, label }) => (
  <div className="flex items-center gap-2">
    <div className={clsx("w-4 h-4 rounded-full flex items-center justify-center border", active ? "border-groww-primary bg-groww-primary text-white" : "border-gray-300 text-transparent")}>
      <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
      </svg>
    </div>
    <span className={clsx("text-sm", active ? "text-groww-dark font-medium" : "text-gray-500")}>{label}</span>
  </div>
);
