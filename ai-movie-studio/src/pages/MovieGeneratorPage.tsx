import { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api, ApiError } from '@/lib/api';

export function MovieGeneratorPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('project');

  const [title, setTitle] = useState('');
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(15);
  const [error, setError] = useState<string | null>(null);

  const createStory = useMutation({
    mutationFn: api.intelligence.createStory,
    onSuccess: (story) => navigate(`/scenes?story=${story.id}`),
    onError: (err) => setError(err instanceof ApiError ? err.message : 'Failed to generate movie'),
  });

  if (!projectId) {
    return (
      <div className="max-w-md">
        <h1 className="text-2xl font-semibold mb-2">Movie Generator</h1>
        <p className="text-sm text-muted-foreground mb-4">
          Pick a project first to generate a movie into.
        </p>
        <Link to="/projects">
          <Button variant="primary">Go to Projects</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold mb-1">Movie Generator</h1>
      <p className="text-sm text-muted-foreground mb-8">
        Describe the movie you want and we'll plan the scenes and characters.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          createStory.mutate({
            project_id: Number(projectId),
            title: title || 'Untitled Movie',
            synopsis: prompt,
            estimated_duration_minutes: duration,
          });
        }}
        className="glass-card p-6 space-y-4"
      >
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5" htmlFor="title">
            Title (optional)
          </label>
          <input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full h-10 px-3 rounded-lg bg-secondary border border-input text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        <div>
          <label className="block text-sm text-muted-foreground mb-1.5" htmlFor="prompt">
            Movie prompt
          </label>
          <textarea
            id="prompt"
            required
            rows={5}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A team of astronauts on Mars discovers an ancient alien artifact..."
            className="w-full px-3 py-2 rounded-lg bg-secondary border border-input text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
          />
        </div>

        <div>
          <label className="block text-sm text-muted-foreground mb-1.5" htmlFor="duration">
            Target length (minutes)
          </label>
          <input
            id="duration"
            type="number"
            min={1}
            max={60}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-32 h-10 px-3 rounded-lg bg-secondary border border-input text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        <Button type="submit" variant="primary" disabled={createStory.isPending}>
          <Sparkles size={16} className="mr-1.5" />
          {createStory.isPending ? 'Generating...' : 'Generate Movie'}
        </Button>
      </form>
    </div>
  );
}
