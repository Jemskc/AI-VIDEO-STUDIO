import { create } from 'zustand';

export interface Project {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  status: 'draft' | 'rendering' | 'completed';
  progress: number;
  createdAt: string;
  updatedAt: string;
}

interface ProjectState {
  projects: Project[];
  activeProject: Project | null;
  setProjects: (projects: Project[]) => void;
  setActiveProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
}

const mockProjects: Project[] = [
  {
    id: '1',
    name: 'Cyberpunk Short Film',
    description: 'A futuristic tale of AI and humanity',
    thumbnail: '/thumbnails/cyberpunk.jpg',
    status: 'rendering',
    progress: 67,
    createdAt: '2024-01-15',
    updatedAt: '2024-01-20',
  },
  {
    id: '2',
    name: 'Nature Documentary',
    description: 'Exploring the wonders of wildlife',
    thumbnail: '/thumbnails/nature.jpg',
    status: 'completed',
    progress: 100,
    createdAt: '2024-01-10',
    updatedAt: '2024-01-18',
  },
  {
    id: '3',
    name: 'Product Commercial',
    description: '30-second advertisement for tech product',
    thumbnail: '/thumbnails/commercial.jpg',
    status: 'draft',
    progress: 25,
    createdAt: '2024-01-20',
    updatedAt: '2024-01-21',
  },
];

export const useProjectStore = create<ProjectState>((set) => ({
  projects: mockProjects,
  activeProject: null,
  setProjects: (projects) => set({ projects }),
  setActiveProject: (project) => set({ activeProject: project }),
  addProject: (project) =>
    set((state) => ({ projects: [...state.projects, project] })),
  updateProject: (id, updates) =>
    set((state) => ({
      projects: state.projects.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
    })),
  deleteProject: (id) =>
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
    })),
}));
