import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/auth';
import wsService from '../services/websocket';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    if (authService.isAuthenticated()) {
      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        const token = localStorage.getItem('token');
        if (token) {
          wsService.connect(token);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        authService.logout();
        wsService.disconnect();
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    const token = await authService.login(email, password);
    const userData = await authService.getCurrentUser();
    setUser(userData);
    if (token) {
      wsService.connect(token);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    wsService.disconnect();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
