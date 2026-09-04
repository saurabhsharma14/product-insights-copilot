import React from 'react';
import clsx from 'clsx';
import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react';

interface ProgressStepProps {
  status: 'pending' | 'active' | 'done' | 'error';
  label: string;
  description?: string;
  isLast?: boolean;
}

export const ProgressStep: React.FC<ProgressStepProps> = ({ status, label, description, isLast }) => {
  return (
    <div className="relative flex gap-4">
      {/* Line connecting steps */}
      {!isLast && (
        <div className="absolute left-[11px] top-8 bottom-[-16px] w-[2px] bg-gray-200" />
      )}
      
      {/* Icon */}
      <div className="relative z-10 flex-shrink-0 mt-1">
        {status === 'done' && <CheckCircle className="w-6 h-6 text-green-500 bg-white" />}
        {status === 'active' && <Loader2 className="w-6 h-6 text-groww-primary animate-spin bg-white" />}
        {status === 'pending' && <Circle className="w-6 h-6 text-gray-300 bg-white" />}
        {status === 'error' && <AlertCircle className="w-6 h-6 text-red-500 bg-white" />}
      </div>
      
      {/* Content */}
      <div className={clsx("pb-8", {
        'opacity-50': status === 'pending'
      })}>
        <h4 className={clsx("font-medium", {
          'text-gray-900': status === 'done' || status === 'active',
          'text-gray-500': status === 'pending',
          'text-red-600': status === 'error',
        })}>
          {label}
        </h4>
        {description && (
          <p className="mt-1 text-sm text-gray-500">
            {description}
          </p>
        )}
      </div>
    </div>
  );
};
