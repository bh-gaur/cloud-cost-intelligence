/**
 * Safe numeric & currency formatters for FinOps telemetry.
 * Prevents runtime TypeErrors if monetary Decimals are serialized as strings.
 */

export const toNumber = (val: number | string | null | undefined, fallback = 0): number => {
  if (val === null || val === undefined) return fallback;
  const num = Number(val);
  return isNaN(num) ? fallback : num;
};

export const getLiveInrRate = (): number => {
  const cached = localStorage.getItem('usd_inr_rate');
  return cached ? parseFloat(cached) : 83.5;
};

export const formatCurrency = (
  val: number | string | null | undefined,
  decimals = 2,
  currencyOverride?: 'USD' | 'INR'
): string => {
  const num = toNumber(val);
  const currency = currencyOverride || (localStorage.getItem('preferred_currency') as 'USD' | 'INR') || 'USD';

  if (currency === 'INR') {
    const rate = getLiveInrRate();
    const inrAmount = num * rate;
    return `₹${inrAmount.toLocaleString('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })}`;
  }

  return `$${num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}`;
};

export const formatPercent = (
  val: number | string | null | undefined,
  decimals = 1
): string => {
  const num = toNumber(val);
  return `${num.toFixed(decimals)}%`;
};

export const formatNumber = (
  val: number | string | null | undefined,
  decimals = 0
): string => {
  const num = toNumber(val);
  return num.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

