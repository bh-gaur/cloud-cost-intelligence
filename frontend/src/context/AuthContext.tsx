import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../api/authApi';
import { organizationApi } from '../api/organizationApi';
import type { User, OrganizationMember } from '../types';

interface AuthContextType {
  user: User | null;
  organizations: OrganizationMember[];
  activeOrgId: string | null;
  activeOrg: OrganizationMember | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (credentials: { email: string; password: string }) => Promise<void>;
  register: (userData: { email: string; password: string; full_name?: string; org_name?: string; role_name?: string }) => Promise<void>;
  switchOrganization: (orgId: string) => Promise<void>;
  refetchOrganizations: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMember[]>([]);
  const [activeOrgId, setActiveOrgId] = useState<string | null>(
    localStorage.getItem('active_org_id')
  );
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchUserAndOrgs = async () => {
    try {
      const userRes = await authApi.getCurrentUser();
      if (userRes.success && userRes.data) {
        setUser(userRes.data);
        const orgRes = await organizationApi.getMyOrganizations();
        if (orgRes.success && orgRes.data) {
          setOrganizations(orgRes.data);
          // Set active org if not set or invalid
          const stored = localStorage.getItem('active_org_id');
          const validStored = orgRes.data.find((o) => o.organization_id === stored);
          if (validStored) {
            setActiveOrgId(validStored.organization_id);
          } else if (orgRes.data.length > 0) {
            const defaultMember = orgRes.data.find((o) => o.is_default) || orgRes.data[0];
            localStorage.setItem('active_org_id', defaultMember.organization_id);
            setActiveOrgId(defaultMember.organization_id);
          } else {
            localStorage.removeItem('active_org_id');
            setActiveOrgId(null);
          }
        }
      } else {
        authApi.logout();
        localStorage.removeItem('active_org_id');
        setUser(null);
        setOrganizations([]);
        setActiveOrgId(null);
      }
    } catch (err) {
      console.error('Auth initialization error:', err);
      authApi.logout();
      localStorage.removeItem('active_org_id');
      setUser(null);
      setOrganizations([]);
      setActiveOrgId(null);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      await fetchUserAndOrgs();
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: { email: string; password: string }) => {
    setIsLoading(true);
    try {
      // Clear stale active_org_id from previous session before fetching user orgs
      localStorage.removeItem('active_org_id');
      setActiveOrgId(null);

      const res = await authApi.login(credentials);
      if (res.success && res.data) {
        localStorage.setItem('access_token', res.data.access_token);
        localStorage.setItem('refresh_token', res.data.refresh_token);

        await fetchUserAndOrgs();
      } else {
        throw new Error(res.error?.message || 'Login failed');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (userData: { email: string; password: string; full_name?: string; org_name?: string; role_name?: string }) => {
    setIsLoading(true);
    try {
      const res = await authApi.register(userData);
      if (!res.success) {
        throw new Error(res.error?.message || 'Registration failed');
      }
      await login({ email: userData.email, password: userData.password });
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = async (orgId: string) => {
    try {
      const res = await organizationApi.switchOrganization(orgId);
      if (res.success) {
        localStorage.setItem('active_org_id', orgId);
        setActiveOrgId(orgId);
      }
    } catch (err) {
      console.error('Failed to switch organization:', err);
      throw err;
    }
  };

  const refetchOrganizations = async () => {
    await fetchUserAndOrgs();
  };

  const logout = () => {
    authApi.logout();
    localStorage.removeItem('active_org_id');
    setUser(null);
    setOrganizations([]);
    setActiveOrgId(null);
    window.location.href = '/login';
  };

  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'ADMIN';
  const activeOrg = organizations.find((o) => o.organization_id === activeOrgId) || null;

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        activeOrgId,
        activeOrg,
        isAuthenticated,
        isAdmin,
        isLoading,
        login,
        register,
        switchOrganization,
        refetchOrganizations,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

