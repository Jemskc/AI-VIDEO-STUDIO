import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Download, PlayCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api, storageUrl, ApiError } from '@/lib/api';

const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled']);

export function RenderQueuePage() {
  const [searchParams] = useSearchParams();
  const storyId = searchParams.get('story');
  const [jobId, setJobId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: blueprint } = useQuery({
    queryKey: ['blueprint', storyId],
    queryFn: () => api.intelligence.getBlueprint(Number(storyId)),
    enabled: !!storyId,
  });

  const startRender = useMutation({
    mutationFn: () =>
      api.render.createJob({
        project_id: blueprint!.story.project_id,
        job_type: 'movie',
        parameters: { story_id: Number(storyId) },
      }),
    onSuccess: (job) => setJobId(job.id),
    onError: (err) => setError(err instanceof ApiError ? err.message : 'Failed to start render'),
  });

  const { data: job } = useQuery({
    queryKey: ['render-job', jobId],
    queryFn: () => api.render.getJob(jobId!),
    enabled: jobId !== null,
    refetchInterval: (query) => (query.state.data && TERMINAL_STATUSES.has(query.state.data.status) ? false : 1500),
  });

  if (!storyId) {
    return (
      <div className="max-w-md">
        <h1 className="text-2xl font-semibold mb-2">Render Queue</h1>
        <p className="text-sm text-muted-foreground mb-4">
          Generate a movie and view its scenes first.
        </p>
        <Link to="/movie-generator">
          <Button variant="primary">Go to Movie Generator</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold mb-1">Render Queue</h1>
      <p className="text-sm text-muted-foreground mb-8">
        {blueprint ? `${blueprint.story.title} · ${blueprint.scene_count} scenes` : 'Loading...'}
      </p>

      {!job && (
        <Button variant="primary" disabled={startRender.isPending} onClick={() => startRender.mutate()}>
          <PlayCircle size={16} className="mr-1.5" />
          {startRender.isPending ? 'Starting...' : 'Start Render'}
        </Button>
      )}

      {error && <p className="text-sm text-destructive mt-4">{error}</p>}

      {job && (
        <div className="glass-card p-6 mt-2 space-y-4">
          <div className="flex items-center justify-between text-sm">
            <span className="capitalize">{job.status.replace('_', ' ')}</span>
            <span className="text-muted-foreground">{job.progress}%</span>
          </div>

          <div className="h-2 rounded-full bg-secondary overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            />
          </div>

          {job.status === 'failed' && (
            <p className="text-sm text-destructive">{job.error_message || 'Render failed.'}</p>
          )}

          {job.status === 'completed' && job.output_url && (
            <div className="space-y-3">
              <video controls className="w-full rounded-lg" src={storageUrl(job.output_url)} />
              <a href={storageUrl(job.output_url)} download>
                <Button variant="outline" size="sm">
                  <Download size={14} className="mr-1.5" /> Download
                </Button>
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
