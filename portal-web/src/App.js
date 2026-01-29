import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './components/Notification';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Materials = lazy(() => import('./pages/Materials'));
const Projects = lazy(() => import('./pages/Projects'));
const Warehouses = lazy(() => import('./pages/Warehouses'));
const Documents = lazy(() => import('./pages/Documents'));
const DocumentAnnotate = lazy(() => import('./pages/DocumentAnnotate'));
const Transfers = lazy(() => import('./pages/Transfers'));
const Reports = lazy(() => import('./pages/Reports'));

// Loading component for Suspense fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
      <p className="mt-4 text-gray-600">Loading...</p>
    </div>
  </div>
);

// Skeleton loader for content areas
const ContentLoader = () => (
  <div className="p-6 animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      {[1, 2, 3].map(i => (
        <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
      ))}
    </div>
    <div className="h-64 bg-gray-200 rounded-lg"></div>
  </div>
);

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Suspense fallback={<ContentLoader />}>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/materials" element={<Materials />} />
                        <Route path="/projects" element={<Projects />} />
                        <Route path="/warehouses" element={<Warehouses />} />
                        <Route path="/transfers" element={<Transfers />} />
                        <Route path="/documents" element={<Documents />} />
                        <Route path="/documents/:documentId/annotate" element={<DocumentAnnotate />} />
                        <Route path="/reports" element={<Reports />} />
                      </Routes>
                    </Suspense>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </NotificationProvider>
    </AuthProvider>
  );
}

export default App;
