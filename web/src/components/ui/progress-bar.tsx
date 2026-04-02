export function ProgressBar({
  percent,
  label,
  stepInfo,
}: {
  percent: number;
  label?: string;
  stepInfo?: string;
}) {
  return (
    <div className="w-full">
      {label && (
        <p className="mb-1 text-sm font-medium text-gray-600">{label}</p>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-2 rounded-full bg-brand-600 transition-all duration-500 ease-out"
          style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
        />
      </div>
      {stepInfo && (
        <p className="mt-1 text-xs text-gray-400">{stepInfo}</p>
      )}
    </div>
  );
}
