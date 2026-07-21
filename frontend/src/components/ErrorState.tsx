import { Card } from "./ui/Card";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", message, onRetry }: ErrorStateProps) {
  return (
    <Card className="border-rose-200 bg-rose-50">
      <div className="px-5 py-6 text-center">
        <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-rose-100 text-2xl">
          ⚠️
        </div>
        <h3 className="text-base font-semibold text-rose-800">{title}</h3>
        <p className="mx-auto mt-1 max-w-md text-sm text-rose-700">{message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-4 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 focus:outline-none focus:ring-2 focus:ring-rose-400"
          >
            Try again
          </button>
        )}
      </div>
    </Card>
  );
}
