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

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
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
