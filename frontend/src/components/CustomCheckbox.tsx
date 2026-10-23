import React from "react";

interface CustomCheckboxProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  className?: string;
}

export const CustomCheckbox: React.FC<CustomCheckboxProps> = ({ checked, onChange, label, className = "" }) => {
  return (
    <label className={`flex items-center space-x-3 cursor-pointer ${className}`}>
      <div className="relative">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="sr-only" />
        <div
          className={`
          w-5 h-5 rounded border-2 transition-all duration-200 flex items-center justify-center
          ${
            checked
              ? "bg-blue-600 border-blue-600 text-white"
              : "bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500"
          }
        `}
        >
          {checked && (
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clipRule="evenodd"
              />
            </svg>
          )}
        </div>
      </div>
      <span className="text-sm text-gray-700 dark:text-gray-300 select-none">{label}</span>
    </label>
  );
};
