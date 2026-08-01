import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';

export function ProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [genre, setGenre] = useState('');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: api.projects.list,
  });

  const createProject = useMutation({
    mutationFn: api.projects.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowForm(false);
      setTitle('');
      setGenre('');
    },
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">Every movie you're making starts here.</p>
        </div>
        <Button variant="primary" onClick={() => setShowForm((v) => !v)}>
          <Plus size={16} className="mr-1.5" /> New Project
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createProject.mutate({ title, genre: genre || undefined });
          }}
          className="glass-card p-6 mb-8 space-y-4 max-w-md"
        >
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5" htmlFor="title">
              Title
            </label>
            <input
              id="title"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-secondary border border-input text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5" htmlFor="genre">
              Genre (optional)
            </label>
            <input
              id="genre"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
              className="w-full h-10 px-3 rounded-lg bg-secondary border border-input text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>
          <Button type="submit" variant="primary" disabled={createProject.isPending}>
            {createProject.isPending ? 'Creating...' : 'Create'}
          </Button>
        </form>
      )}

      {isLoading && <p className="text-sm text-muted-foreground">Loading projects...</p>}

      {projects && projects.length === 0 && (
        <p className="text-sm text-muted-foreground">No projects yet. Create one to get started.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects?.map((project) => (
          <div key={project.id} className="glass-card p-5 flex flex-col gap-3">
            <div>
              <h3 className="font-medium">{project.title}</h3>
              {project.genre && <p className="text-xs text-muted-foreground mt-0.5">{project.genre}</p>}
            </div>
            <p className="text-xs text-muted-foreground flex-1">
              {project.description || 'No description yet.'}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/movie-generator?project=${project.id}`)}
            >
              <Sparkles size={14} className="mr-1.5" /> Generate Movie
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
