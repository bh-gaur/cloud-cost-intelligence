import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TableProperties,
  Layers,
  Building2,
  Globe2,
  FileBarChart2,
  TrendingDown,
  BellRing,
  Settings,
  Users,
  ShieldCheck,
  LogOut,
  Cloud,
  Tag,
} from 'lucide-react';
import { authApi } from '../api/authApi';
import { ConfirmModal } from './ConfirmModal';

interface SidebarProps {
  userRole?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ userRole = 'USER' }) => {
  const isAdmin = userRole === 'ADMIN';
  const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Costs Explorer', path: '/costs', icon: TableProperties },
    { label: 'Services', path: '/services', icon: Layers },
    { label: 'AWS Accounts', path: '/accounts', icon: Building2 },
    { label: 'Regions', path: '/regions', icon: Globe2 },
    { label: 'Reports', path: '/reports', icon: FileBarChart2 },
    { label: 'Optimization', path: '/optimization', icon: TrendingDown },
    { label: 'Tag Governance', path: '/tagging', icon: Tag },
    { label: 'Alerts & Budgets', path: '/alerts', icon: BellRing },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const adminItems = [
    { label: 'Users Management', path: '/admin/users', icon: Users },
    { label: 'System & Audit', path: '/admin/system', icon: ShieldCheck },
  ];

  const handleConfirmSignOut = () => {
    authApi.logout();
    window.location.href = '/login';
  };

  return (
    <aside className="sidebar-container w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen select-none transition-colors">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-slate-200 dark:border-slate-800 gap-3">
        <div className="p-2.5 bg-gradient-to-tr from-blue-600 to-sky-500 text-white rounded-xl shadow-md shadow-blue-500/20 flex items-center justify-center shrink-0">
          <Cloud className="w-5 h-5 text-white stroke-[2.25]" />
        </div>
        <div>
          <h1 className="font-bold text-sm tracking-tight text-slate-900 dark:text-white leading-tight">
            AWS Cost
          </h1>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider uppercase">
            Intelligence
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 py-1 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
          FinOps Platform
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        {isAdmin && (
          <>
            <div className="pt-4 px-3 py-1 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Administration
            </div>
            {adminItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${isActive
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </>
        )}
      </nav>

      {/* Footer / Logout */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setShowSignOutConfirm(true)}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>

      <ConfirmModal
        isOpen={showSignOutConfirm}
        onClose={() => setShowSignOutConfirm(false)}
        onConfirm={handleConfirmSignOut}
        title="Sign Out Confirmation"
        message="Are you sure you want to sign out of your FinOps active session?"
        confirmText="Sign Out"
        cancelText="Cancel"
        variant="danger"
      />
    </aside>
  );
};

