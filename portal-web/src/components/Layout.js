import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Έργα', href: '/projects', icon: '🏗️' },
  { name: 'Αποθήκες', href: '/warehouses', icon: '🏭' },
  { name: 'Υλικά', href: '/materials', icon: '📦' },
  { name: 'Μεταφορές', href: '/transfers', icon: '🚚' },
  { name: 'Έγγραφα', href: '/documents', icon: '📄' },
  { name: 'Αναφορές', href: '/reports', icon: '📈' },
];

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Sidebar για desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 bg-primary-800">
          <div className="flex items-center h-16 flex-shrink-0 px-4 bg-primary-900">
            <h1 className="text-white text-xl font-bold">ErgoLab</h1>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto">
            <nav className="flex-1 px-2 py-4 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      group flex items-center px-2 py-2 text-sm font-medium rounded-md
                      ${isActive 
                        ? 'bg-primary-900 text-white' 
                        : 'text-primary-100 hover:bg-primary-700'
                      }
                    `}
                  >
                    <span className="mr-3 text-xl">{item.icon}</span>
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-primary-700 p-4">
            <div className="flex items-center w-full">
              <div className="flex-1">
                <p className="text-sm font-medium text-white">{user?.full_name}</p>
                <p className="text-xs text-primary-300">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="ml-3 text-primary-300 hover:text-white"
              >
                🚪
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
