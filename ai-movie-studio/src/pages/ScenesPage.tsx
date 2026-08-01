import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Clapperboard, Users } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';

export function ScenesPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const storyId = searchParams.get('story');

  const { data: blueprint, isLoading, error } = useQuery({
    queryKey: ['blueprint', storyId],
    queryFn: () => api.intelligence.getBlueprint(Number(storyId)),
    enabled: !!storyId,
  });

  if (!storyId) {
    return (
      <div className="max-w-md">
        <h1 className="text-2xl font-semibold mb-2">Scenes</h1>
        <p className="text-sm text-muted-foreground mb-4">
          Generate a movie first to see its scenes here.
        </p>
        <Link to="/movie-generator">
          <Button variant="primary">Go to Movie Generator</Button>
        </Link>
      </div>
    );
  }

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading scenes...</p>;
  if (error || !blueprint) return <p className="text-sm text-destructive">Couldn't load this story.</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">{blueprint.story.title}</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {blueprint.scene_count} scenes &middot; {blueprint.total_estimated_duration_min.toFixed(1)}{' '}
            min &middot; {blueprint.story.genre} &middot; {blueprint.story.mood}
          </p>
        </div>
        <Button variant="primary" onClick={() => navigate(`/render-queue?story=${storyId}`)}>
          Render Movie
        </Button>
      </div>

      <div className="glass-card p-5 mb-6">
        <h2 className="flex items-center gap-2 text-sm font-medium mb-3">
          <Users size={16} /> Characters
        </h2>
        <div className="flex flex-wrap gap-2">
          {blueprint.characters.map((c) => (
            <span key={c.id} className="text-xs px-3 py-1.5 rounded-full bg-secondary">
              {c.name} <span className="text-muted-foreground">&middot; {c.role}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {blueprint.scenes.map((scene) => (
          <div key={scene.id} className="glass-card p-4 flex gap-4">
            <div className="w-9 h-9 rounded-lg bg-secondary flex items-center justify-center flex-shrink-0">
              <Clapperboard size={16} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium">{scene.title || scene.slugline}</p>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{scene.image_prompt}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
