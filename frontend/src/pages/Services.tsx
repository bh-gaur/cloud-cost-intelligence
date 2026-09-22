import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layers, ArrowUpRight, ArrowDownRight, X, Globe2, Calendar } from 'lucide-react';
import { serviceApi } from '../api/serviceApi';
import { useDashboardContext } from '../components/Layout';
import { useCurrency } from '../context/CurrencyContext';
import { getServiceColor } from '../constants/serviceColors';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { formatCurrency } from '../utils/formatters';

export const Services: React.FC = () => {
  const { selectedAccount } = useDashboardContext();
  const { currency } = useCurrency();
  const [range, setRange] = useState('30d');
  const [selectedService, setSelectedService] = useState<string | null>(null);

  const { data: servicesResp, isLoading } = useQuery({
    queryKey: ['servicesBreakdown', selectedAccount, range],
    queryFn: () => serviceApi.getServices(selectedAccount, range),
  });

  const { data: detailResp } = useQuery({
    queryKey: ['serviceDetail', selectedService, selectedAccount],
    queryFn: () => serviceApi.getServiceDetail(selectedService!, selectedAccount),
    enabled: !!selectedService,
  });

  const services = servicesResp?.data || [];
  const detail = detailResp?.data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
            AWS Services Spend Breakdown
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Analyze spending concentration, growth trends, and regional distribution per service
          </p>
        </div>

        <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-800 p-1 bg-white dark:bg-slate-900">
          {(['7d', '14d', '30d', '90d'] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1 text-xs font-semibold rounded-md uppercase transition-colors ${range === r
                ? 'bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-400'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 uppercase font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3 px-4">Service Name</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Period Cost ({currency})</th>
                <th className="py-3 px-4">Previous Period</th>
                <th className="py-3 px-4">Variance</th>
                <th className="py-3 px-4">% of Total</th>
                <th className="py-3 px-4">Trend</th>
                <th className="py-3 px-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {services.map((s) => (
                <tr key={s.service} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                  <td className="py-3 px-4 font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: getServiceColor(s.service) }}
                    />
                    <span>{s.service}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-600 dark:text-slate-400">
                    <span className="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 font-medium text-[11px]">
                      {s.category}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900 dark:text-white">
                    {formatCurrency(s.current_cost)}
                  </td>
                  <td className="py-3 px-4 text-slate-500">
                    {formatCurrency(s.previous_cost)}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`font-semibold ${s.trend === 'UP'
                        ? 'text-rose-600 dark:text-rose-400'
                        : s.trend === 'DOWN'
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : 'text-slate-500'
                        }`}
                    >
                      {s.trend === 'UP' ? '+' : ''}
                      {formatCurrency(s.difference)} ({Number(s.percentage_change).toFixed(1)}%)
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-700 dark:text-slate-300 font-medium">
                    {Number(s.percentage_of_total).toFixed(1)}%
                  </td>
                  <td className="py-3 px-4">
                    {s.trend === 'UP' && <ArrowUpRight className="w-4 h-4 text-rose-500" />}
                    {s.trend === 'DOWN' && <ArrowDownRight className="w-4 h-4 text-emerald-500" />}
                    {s.trend === 'FLAT' && <span className="text-slate-400">—</span>}
                  </td>
                  <td className="py-3 px-4">
                    <button
                      onClick={() => setSelectedService(s.service)}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-500"
                    >
                      Drilldown →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Drilldown Modal */}
      {selectedService && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getServiceColor(selectedService) }}
                />
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {selectedService} Drilldown
                </h3>
              </div>
              <button
                onClick={() => setSelectedService(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3 bg-blue-50 dark:bg-blue-950/30 rounded-xl border border-blue-100 dark:border-blue-900/40">
                <span className="text-xs text-blue-700 dark:text-blue-300 font-medium">
                  30-Day Cumulative Cost
                </span>
                <p className="text-xl font-bold text-blue-900 dark:text-blue-200 mt-0.5">
                  {formatCurrency(detail?.total_30d_cost)}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                  <Globe2 className="w-3.5 h-3.5" /> Regional Distribution
                </h4>
                <div className="space-y-2">
                  {(detail?.regional_distribution || []).map((r: any) => (
                    <div
                      key={r.region}
                      className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 flex justify-between items-center text-xs"
                    >
                      <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                        {r.region}
                      </span>
                      <div className="flex items-center gap-3 font-semibold">
                        <span className="text-slate-900 dark:text-white">{formatCurrency(r.cost)}</span>
                        <span className="text-slate-400 text-[10px]">({r.percentage}%)</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

