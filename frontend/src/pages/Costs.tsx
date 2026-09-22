import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Download,
  Search,
  Filter,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Layers,
  Calendar,
  RotateCcw,
} from 'lucide-react';
import { costApi } from '../api/costApi';
import { serviceApi } from '../api/serviceApi';
import { regionApi } from '../api/regionApi';
import { useDashboardContext } from '../components/Layout';
import { useCurrency } from '../context/CurrencyContext';
import { getServiceColor } from '../constants/serviceColors';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { formatCurrency } from '../utils/formatters';

export const Costs: React.FC = () => {
  const { selectedAccount, accounts } = useDashboardContext();
  const { currency } = useCurrency();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [search, setSearch] = useState('');
  const [service, setService] = useState('all');
  const [region, setRegion] = useState('all');
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Dynamic services and regions
  const { data: servicesResp } = useQuery({
    queryKey: ['availableServices', selectedAccount],
    queryFn: () => serviceApi.getServices(selectedAccount, '90d'),
  });

  const { data: regionsResp } = useQuery({
    queryKey: ['availableRegions'],
    queryFn: () => regionApi.getRegions('90d'),
  });

  const availableServices = servicesResp?.data || [];
  const availableRegions = regionsResp?.data || [];

  const { data: costsResp, isLoading } = useQuery({
    queryKey: ['costRecords', page, pageSize, selectedAccount, service, region, category, search, sortBy, sortOrder],
    queryFn: () =>
      costApi.getCosts({
        page,
        pageSize,
        accountId: selectedAccount,
        service,
        region,
        category,
        search: search || undefined,
        sortBy,
        sortOrder,
      }),
  });

  const records = costsResp?.data || [];
  const meta = costsResp?.meta;

  const hasActiveFilters = search !== '' || service !== 'all' || region !== 'all' || category !== 'all';

  const resetFilters = () => {
    setSearch('');
    setService('all');
    setRegion('all');
    setCategory('all');
    setPage(1);
  };

  const handleDownloadCsv = () => {
    const url = costApi.getCsvDownloadUrl({
      accountId: selectedAccount,
      service,
      region,
      search: search || undefined,
    });
    window.open(url, '_blank');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            Cost & Usage Records
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Granular line-item spending across services, resources, and accounts
          </p>
        </div>

        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              onClick={resetFilters}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg transition-colors cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Filters</span>
            </button>
          )}
          <button
            onClick={handleDownloadCsv}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors shadow-sm cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Download Filtered CSV</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Search service or resource..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Service Filter (Dynamically Populated) */}
          <div>
            <select
              value={service}
              onChange={(e) => {
                setService(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="all">All Services ({availableServices.length})</option>
              {availableServices.map((s) => (
                <option key={s.service} value={s.service}>
                  {s.service}
                </option>
              ))}
            </select>
          </div>

          {/* Region Filter (Dynamically Populated) */}
          <div>
            <select
              value={region}
              onChange={(e) => {
                setRegion(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="all">All Regions ({availableRegions.length})</option>
              {availableRegions.map((r) => (
                <option key={r.region} value={r.region}>
                  {r.region}
                </option>
              ))}
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="w-full px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="all">All Categories</option>
              <option value="Compute">Compute</option>
              <option value="Storage">Storage</option>
              <option value="Database">Database</option>
              <option value="Networking">Networking</option>
              <option value="Containers">Containers</option>
              <option value="Serverless">Serverless</option>
              <option value="Monitoring">Monitoring</option>
              <option value="Security">Security</option>
              <option value="Analytics">Analytics</option>
              <option value="Other">Other</option>
            </select>
          </div>

          {/* Sort Order */}
          <div className="flex gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="flex-1 px-2.5 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
            >
              <option value="date">Date</option>
              <option value="cost">Cost</option>
              <option value="service">Service</option>
              <option value="account_id">Account</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              className="px-2.5 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg hover:bg-slate-200 text-xs flex items-center gap-1 cursor-pointer"
              title="Toggle Sort Order"
            >
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span className="uppercase">{sortOrder}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {isLoading ? (
          <div className="p-6">
            <LoadingSkeleton rows={8} />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4">Region</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Resource ID</th>
                  <th className="py-3 px-4">Usage</th>
                  <th className="py-3 px-4">Cost ({currency})</th>
                  <th className="py-3 px-4">Tags</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {records.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 px-4 font-medium text-slate-700 dark:text-slate-300">
                      {r.date}
                    </td>
                    <td className="py-2.5 px-4">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {r.account_name}
                      </span>
                      <span className="block text-[10px] text-slate-400">
                        ...{r.account_id.slice(-4)}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
                      {r.region}
                    </td>
                    <td className="py-2.5 px-4">
                      <div className="flex items-center gap-1.5">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: getServiceColor(r.service) }}
                        />
                        <span className="font-medium text-slate-900 dark:text-white truncate max-w-[160px]">
                          {r.service}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 ml-3.5">
                        {r.service_category}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 font-mono text-[10px] text-slate-500 truncate max-w-[140px]">
                      {r.resource_id ? r.resource_id.split(':').pop() : '—'}
                    </td>
                    <td className="py-2.5 px-4 text-slate-600 dark:text-slate-300">
                      {Number(r.usage_quantity).toFixed(1)} {r.usage_unit}
                    </td>
                    <td className="py-2.5 px-4 font-bold text-slate-900 dark:text-white">
                      {formatCurrency(r.cost)}
                    </td>
                    <td className="py-2.5 px-4">
                      {r.tags && Object.keys(r.tags).length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {r.tags.Environment && (
                            <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 rounded">
                              {r.tags.Environment}
                            </span>
                          )}
                          {r.tags.Team && (
                            <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 rounded">
                              {r.tags.Team}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-[10px] text-rose-500 font-medium">Untagged</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="py-3 px-4 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
          <div>
            Showing <span className="font-semibold text-slate-900 dark:text-white">{records.length}</span> of{' '}
            <span className="font-semibold text-slate-900 dark:text-white">{meta?.total_count || 0}</span> records
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page {page} of {meta?.total_pages || 1}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= (meta?.total_pages || 1)}
              className="p-1 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

