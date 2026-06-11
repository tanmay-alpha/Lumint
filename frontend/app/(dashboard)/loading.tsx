export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--canvas)]">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
        <p className="text-sm text-[var(--text-3)] font-medium">Loading Lumint...</p>
      </div>
    </div>
  );
}