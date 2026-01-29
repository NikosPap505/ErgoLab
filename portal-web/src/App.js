import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { NotificationProvider } from './components/Notification';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Materials from './pages/Materials';
import Projects from './pages/Projects';
import Warehouses from './pages/Warehouses';
import Documents from './pages/Documents';
import DocumentAnnotate from './pages/DocumentAnnotate';

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
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/materials" element={<Materials />} />
                      <Route path="/projects" element={<Projects />} />
                      <Route path="/warehouses" element={<Warehouses />} />
                      <Route path="/transfers" element={<div className="p-4">Transfers (TODO)</div>} />
                      <Route path="/documents" element={<Documents />} />
                      <Route path="/documents/:documentId/annotate" element={<DocumentAnnotate />} />
                      <Route path="/reports" element={<div className="p-4">Reports (TODO)</div>} />
                    </Routes>
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
