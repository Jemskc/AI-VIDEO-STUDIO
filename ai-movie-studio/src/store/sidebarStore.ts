import { create } from 'zustand';

export interface NavItem {
  id: string;
  label: string;
  icon: string;
  path: string;
}

interface SidebarState {
  isOpen: boolean;
  isCollapsed: boolean;
  activeItem: string;
  toggle: () => void;
  collapse: () => void;
  setActiveItem: (id: string) => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  isOpen: true,
  isCollapsed: false,
  activeItem: 'dashboard',
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  collapse: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
  setActiveItem: (id) => set({ activeItem: id }),
}));
