import React, { createContext, useContext, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { FinOpsCopilot } from './FinOpsCopilot';
import { authApi } from '../api/authApi';
import { awsApi } from '../api/awsApi';
import { apiClient } from '../api/client';


interface DashboardContextType {
  selectedAccount: string;
  setSelectedAccount: (acc: string) => void;
  accounts: Array<{ account_id: string; account_name: string }>;
}

const DashboardContext = createContext<DashboardContextType>({
  selectedAccount: 'all',
  setSelectedAccount: () => { },
  accounts: [],
});

export const useDashboardContext = () => useContext(DashboardContext);

export const Layout: React.FC = () => {
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const location = useLocation();

  const { data: userResp } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
    staleTime: 1000 * 60 * 5,
  });

  const { data: accountsResp } = useQuery({
    queryKey: ['awsAccounts'],
    queryFn: awsApi.getAccounts,
    staleTime: 1000 * 60 * 10,
  });

  const { data: healthResp } = useQuery({
    queryKey: ['healthState'],
    queryFn: async () => {
      const res = await apiClient.get('/health');
      return res.data?.data;
    },
    staleTime: 1000 * 60 * 5,
  });

  const user = userResp?.data;
  const accounts = accountsResp?.data || [];
  const isDemoMode = healthResp?.demo_mode ?? false;

  return (
    <DashboardContext.Provider value={{ selectedAccount, setSelectedAccount, accounts }}>
      <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 overflow-hidden font-sans">
        <Sidebar userRole={user?.role} />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header
            user={user}
            isDemoMode={isDemoMode}
            selectedAccount={selectedAccount}
            onAccountChange={setSelectedAccount}
            accounts={accounts}
          />

          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 12, scale: 0.995 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="h-full"
              >
                <Outlet />
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
        <FinOpsCopilot selectedAccount={selectedAccount} />
      </div>
    </DashboardContext.Provider>
  );
};

