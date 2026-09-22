import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, Calendar } from 'lucide-react';

interface KpiCardProps {
  title: string;
  value: string;
  dateBadge?: string;
  subtitle?: string;
  secondaryText?: string;
  diff?: string;
  percentage?: number | string;
  direction?: 'UP' | 'DOWN' | 'FLAT';
  isInverseTrend?: boolean; // If true, DOWN is good (green), UP is bad (red)
  icon?: React.ReactNode;
  delay?: number;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  dateBadge,
  subtitle,
  secondaryText,
  diff,
  percentage,
  direction,
  isInverseTrend = true,
  icon,
  delay = 0,
}) => {
  const isUp = direction === 'UP';
  const isDown = direction === 'DOWN';

  let badgeColor = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  if (direction) {
    if (isInverseTrend) {
      badgeColor = isUp
        ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900/50'
        : isDown
          ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50'
          : badgeColor;
    } else {
      badgeColor = isUp
        ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/50'
        : isDown
          ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900/50'
          : badgeColor;
    }
  }

  const numPercentage = percentage !== undefined && percentage !== null ? Number(percentage) : undefined;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm hover:shadow-md transition-all duration-300 flex flex-col justify-between"
    >
      <div>
        <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider">{title}</span>
          {icon && <div className="text-slate-400">{icon}</div>}
        </div>

        {dateBadge && (
          <div className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 dark:text-cyan-400 mb-2">
            <Calendar className="w-3 h-3" />
            <span>{dateBadge}</span>
          </div>
        )}

        <div className="flex items-baseline gap-2">
          <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {value}
          </div>
        </div>
      </div>

      {(numPercentage !== undefined || diff || subtitle || secondaryText) && (
        <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 space-y-1 text-xs">
          <div className="flex items-center justify-between gap-2">
            {numPercentage !== undefined && !isNaN(numPercentage) ? (
              <span className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-md ${badgeColor}`}>
                {isUp && <TrendingUp className="w-3.5 h-3.5" />}
                {isDown && <TrendingDown className="w-3.5 h-3.5" />}
                {!isUp && !isDown && <Minus className="w-3.5 h-3.5" />}
                <span>
                  {isUp ? '+' : ''}
                  {numPercentage.toFixed(1)}% {diff ? `(${diff})` : ''}
                </span>
              </span>
            ) : <span />}
            {subtitle && (
              <span className="text-slate-500 dark:text-slate-400 text-right truncate font-medium">{subtitle}</span>
            )}
          </div>
          {secondaryText && (
            <p className="text-[11px] text-slate-400 dark:text-slate-500">{secondaryText}</p>
          )}
        </div>
      )}
    </motion.div>
  );
};
