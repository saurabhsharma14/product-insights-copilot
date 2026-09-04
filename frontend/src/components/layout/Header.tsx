import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center shadow-sm">
      <h1 className="text-xl font-bold text-groww-dark flex items-center gap-2">
        <span className="w-8 h-8 rounded-full bg-groww-primary flex items-center justify-center text-white">G</span>
        Groww Product Feedback Intelligence
      </h1>
    </header>
  );
};
