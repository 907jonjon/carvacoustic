"use client";

import { type InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className = "", ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label
            htmlFor={inputId}
            className="text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={[
            "block w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900",
            "placeholder:text-gray-400",
            "focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500",
            "disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500",
            error ? "border-red-500 focus:border-red-500 focus:ring-red-500" : "",
            className,
          ].join(" ")}
          {...props}
        />
        {hint && !error && (
          <p className="text-xs text-gray-500">{hint}</p>
        )}
        {error && (
          <p className="text-xs text-red-600">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
