import React, { useState, useEffect } from 'react';
import { Edit2, Check, X } from 'lucide-react';
import { clsx } from 'clsx';

interface EditableTextAreaProps {
  initialValue: string;
  onSave: (value: string) => void;
  title: string;
  maxWords?: number;
}

export const EditableTextArea: React.FC<EditableTextAreaProps> = ({ 
  initialValue, 
  onSave, 
  title, 
  maxWords = 250 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(initialValue);
  
  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

  const wordCount = value.trim() ? value.trim().split(/\s+/).length : 0;
  const isOverLimit = maxWords && wordCount > maxWords;

  const handleSave = () => {
    onSave(value);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setValue(initialValue);
    setIsEditing(false);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
        <div className="flex items-center gap-2">
          <span className={clsx("text-xs font-medium", isOverLimit ? "text-red-600" : "text-gray-500")}>
            {wordCount} / {maxWords} words
          </span>
          {!isEditing ? (
            <button 
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
              title="Edit"
            >
              <Edit2 size={16} />
            </button>
          ) : (
            <div className="flex gap-1">
              <button 
                onClick={handleSave}
                className="p-1.5 text-green-600 hover:bg-green-50 rounded-md transition-colors"
                title="Save"
              >
                <Check size={16} />
              </button>
              <button 
                onClick={handleCancel}
                className="p-1.5 text-red-500 hover:bg-red-50 rounded-md transition-colors"
                title="Cancel"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
      
      <div className="p-4 flex-grow">
        {isEditing ? (
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full h-full min-h-[200px] p-2 text-sm text-gray-700 border border-green-500 rounded-md focus:outline-none focus:ring-1 focus:ring-green-500 resize-y"
          />
        ) : (
          <div className="text-sm text-gray-700 whitespace-pre-wrap h-full min-h-[200px] overflow-y-auto">
            {value}
          </div>
        )}
      </div>
    </div>
  );
};
