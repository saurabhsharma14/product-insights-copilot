import React from 'react';
import { clsx } from 'clsx';
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react';

interface TrendBadgeProps {
  trend: string;
}

export const TrendBadge: React.FC<TrendBadgeProps> = ({ trend }) => {
  const normalizedTrend = trend.toLowerCase();
  
  let icon = <Minus size={14} />;
  let colorClass = 'bg-gray-100 text-gray-800';
  
  if (normalizedTrend.includes('increasing')) {
    icon = <TrendingUp size={14} />;
    colorClass = 'bg-red-100 text-red-800'; // Assuming increasing complaints is bad
  } else if (normalizedTrend.includes('decreasing')) {
    icon = <TrendingDown size={14} />;
    colorClass = 'bg-green-100 text-green-800';
  } else if (normalizedTrend.includes('spiking')) {
    icon = <Activity size={14} />;
    colorClass = 'bg-orange-100 text-orange-800';
  }
  
  return (
    <span className={clsx('inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium', colorClass)}>
      {icon}
      {trend}
    </span>
  );
};
