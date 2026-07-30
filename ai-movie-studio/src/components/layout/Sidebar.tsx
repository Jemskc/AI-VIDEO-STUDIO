import React from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  Film, 
  Layers, 
  Users, 
  Clapperboard, 
  Video, 
  Image, 
  Wand2, 
  Package, 
  BarChart3, 
  Settings, 
  HelpCircle,
  Cpu,
  History,
  Download,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';

export interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  category?: 'main' | 'creation' | 'management' | 'system';
}

export const navigationItems: NavItem[] = [
  // Main
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} />, path: '/dashboard', category: 'main' },
  
  // Creation
  { id: 'movie-generator', label: 'Movie Generator', icon: <Sparkles size={18} />, path: '/movie-generator', category: 'creation' },
  { id: 'prompt-builder', label: 'Prompt Builder', icon: <Wand2 size={18} />, path: '/prompt-builder', category: 'creation' },
  { id: 'storyboard', label: 'Storyboard', icon: <Layers size={18} />, path: '/storyboard', category: 'creation' },
  { id: 'characters', label: 'Characters', icon: <Users size={18} />, path: '/characters', category: 'creation' },
  { id: 'scenes', label: 'Scenes', icon: <Clapperboard size={18} />, path: '/scenes', category: 'creation' },
  { id: 'timeline', label: 'Timeline Editor', icon: <Video size={18} />, path: '/timeline', category: 'creation' },
  
  // Management
  { id: 'projects', label: 'Projects', icon: <Film size={18} />, path: '/projects', category: 'management' },
  { id: 'assets', label: 'Assets', icon: <Image size={18} />, path: '/assets', category: 'management' },
  { id: 'templates', label: 'Templates', icon: <Package size={18} />, path: '/templates', category: 'management' },
  { id: 'render-queue', label: 'Render Queue', icon: <Cpu size={18} />, path: '/render-queue', category: 'management' },
  { id: 'exports', label: 'Exports', icon: <Download size={18} />, path: '/exports', category: 'management' },
  { id: 'history', label: 'History', icon: <History size={18} />, path: '/history', category: 'management' },
  
  // System
  { id: 'ai-models', label: 'AI Models', icon: <Cpu size={18} />, path: '/ai-models', category: 'system' },
  { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={18} />, path: '/analytics', category: 'system' },
  { id: 'settings', label: 'Settings', icon: <Settings size={18} />, path: '/settings', category: 'system' },
  { id: 'help', label: 'Help', icon: <HelpCircle size={18} />, path: '/help', category: 'system' },
];

interface SidebarProps {
  className?: string;
  collapsed?: boolean;
  activeItem?: string;
  onItemClick?: (id: string) => void;
}

export function Sidebar({ className, collapsed = false, activeItem = 'dashboard', onItemClick }: SidebarProps) {
  const categories = ['main', 'creation', 'management', 'system'] as const;
  const categoryLabels = {
    main: '',
    creation: 'Creation',
    management: 'Management',
    system: 'System',
  };

  return (
    <motion.aside
      initial={{ width: collapsed ? 80 : 260 }}
      animate={{ width: collapsed ? 80 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        'fixed left-0 top-0 h-full bg-background border-r border-border flex flex-col z-50',
        className
      )}
    >
      {/* Logo */}
      <div className={cn(
        'h-16 flex items-center px-4 border-b border-border',
        collapsed && 'justify-center'
      )}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Film size={18} className="text-white" />
          </div>
          {!collapsed && (
            <span className="font-bold text-lg gradient-text">AI Movie Studio</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {categories.map((category) => {
          const items = navigationItems.filter((item) => item.category === category);
          if (items.length === 0) return null;

          return (
            <div key={category} className="mb-6">
              {!collapsed && categoryLabels[category] && (
                <h3 className="px-4 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                  {categoryLabels[category]}
                </h3>
              )}
              <ul className="space-y-1">
                {items.map((item) => (
                  <li key={item.id}>
                    <button
                      onClick={() => onItemClick?.(item.id)}
                      className={cn(
                        'w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-all duration-200',
                        'hover:bg-accent hover:text-accent-foreground',
                        activeItem === item.id && 'bg-accent text-accent-foreground border-r-2 border-primary',
                        collapsed && 'justify-center px-2'
                      )}
                    >
                      <span className={cn(
                        'flex-shrink-0',
                        activeItem === item.id && 'text-primary'
                      )}>
                        {item.icon}
                      </span>
                      {!collapsed && (
                        <span className="truncate">{item.label}</span>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className={cn(
        'p-4 border-t border-border',
        collapsed && 'px-2'
      )}>
        <div className={cn(
          'flex items-center gap-3',
          collapsed && 'justify-center'
        )}>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-medium text-sm">
            JD
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">John Doe</p>
              <p className="text-xs text-muted-foreground truncate">Pro Plan</p>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
