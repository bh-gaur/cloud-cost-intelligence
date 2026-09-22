import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Globe2 } from 'lucide-react';
import { regionApi } from '../api/regionApi';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { formatCurrency } from '../utils/formatters';

const REGION_NAMES: Record<string, string> = {
  global: 'AWS Global Services (IAM, Route53, CloudFront)',
  Global: 'AWS Global Services (IAM, Route53, CloudFront)',
  'us-east-1': 'US East (N. Virginia)',
  'us-east-2': 'US East (Ohio)',
  'us-west-1': 'US West (N. California)',
  'us-west-2': 'US West (Oregon)',
  'ca-central-1': 'Canada (Central)',
  'eu-west-1': 'Europe (Ireland)',
  'eu-west-2': 'Europe (London)',
  'eu-west-3': 'Europe (Paris)',
  'eu-central-1': 'Europe (Frankfurt)',
  'eu-north-1': 'Europe (Stockholm)',
  'ap-south-1': 'Asia Pacific (Mumbai)',
  'ap-south-2': 'Asia Pacific (Hyderabad)',
  'ap-southeast-1': 'Asia Pacific (Singapore)',
  'ap-southeast-2': 'Asia Pacific (Sydney)',
  'ap-northeast-1': 'Asia Pacific (Tokyo)',
  'ap-northeast-2': 'Asia Pacific (Seoul)',
  'sa-east-1': 'South America (São Paulo)',
  'me-south-1': 'Middle East (Bahrain)',
  'af-south-1': 'Africa (Cape Town)',
};

const getRegionDisplayName = (region: string): string => {
  return REGION_NAMES[region] || REGION_NAMES[region.toLowerCase()] || 'AWS Region / Global Service';
};

export const Regions: React.FC = () => {
  const { data: regionsResp, isLoading } = useQuery({
    queryKey: ['regionsList'],
    queryFn: () => regionApi.getRegions('30d'),
  });

  const regions = regionsResp?.data || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
          AWS Regional Cost Distribution
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Geographic concentration of cloud spending across AWS availability zones and regions
        </p>
      </div>

      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {regions.map((reg) => (
            <div
              key={reg.region}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 rounded-lg">
                  <Globe2 className="w-5 h-5" />
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  {Number(reg.percentage_of_total).toFixed(1)}%
                </span>
              </div>

              <h3 className="text-sm font-bold font-mono text-slate-900 dark:text-white capitalize">
                {reg.region}
              </h3>
              <p className="text-[11px] text-slate-400 mb-4">
                {getRegionDisplayName(reg.region)}
              </p>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs flex justify-between items-baseline">
                <span className="text-slate-500">30-Day Cost:</span>
                <span className="text-base font-bold text-slate-900 dark:text-white">
                  {formatCurrency(reg.cost)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

