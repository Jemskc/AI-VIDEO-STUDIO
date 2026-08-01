import { Sparkles } from 'lucide-react';

export function ComingSoonPage() {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-center gap-3">
      <Sparkles size={32} className="text-muted-foreground" />
      <h2 className="text-lg font-medium">Coming soon</h2>
      <p className="text-sm text-muted-foreground max-w-sm">
        This section isn't built yet. Try Projects, Movie Generator, Scenes, or Render Queue in the
        sidebar.
      </p>
    </div>
  );
}
