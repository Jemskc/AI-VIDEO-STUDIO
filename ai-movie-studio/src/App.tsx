import type { ReactNode } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar, navigationItems } from '@/components/layout/Sidebar';
import { useAuthStore } from '@/store/authStore';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { MovieGeneratorPage } from '@/pages/MovieGeneratorPage';
import { ScenesPage } from '@/pages/ScenesPage';
import { RenderQueuePage } from '@/pages/RenderQueuePage';
import { ComingSoonPage } from '@/pages/ComingSoonPage';

function ProtectedLayout({ children }: { children: ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const navigate = useNavigate();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const activeItem =
    navigationItems.find((item) => location.pathname.startsWith(item.path))?.id ?? 'projects';

  return (
    <div className="min-h-screen">
      <Sidebar
        activeItem={activeItem}
        onItemClick={(id) => {
          const item = navigationItems.find((n) => n.id === id);
          if (item) navigate(item.path);
        }}
      />
      <main className="ml-[260px] min-h-screen p-8">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route
        path="/projects"
        element={
          <ProtectedLayout>
            <ProjectsPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/movie-generator"
        element={
          <ProtectedLayout>
            <MovieGeneratorPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/scenes"
        element={
          <ProtectedLayout>
            <ScenesPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/render-queue"
        element={
          <ProtectedLayout>
            <RenderQueuePage />
          </ProtectedLayout>
        }
      />
      <Route
        path="*"
        element={
          <ProtectedLayout>
            <ComingSoonPage />
          </ProtectedLayout>
        }
      />
    </Routes>
  );
}
