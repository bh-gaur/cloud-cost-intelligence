import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type Currency = 'USD' | 'INR';

interface CurrencyContextType {
  currency: Currency;
  exchangeRate: number;
  isRateLive: boolean;
  setCurrency: (currency: Currency) => void;
  formatCost: (amountInUSD: number | string | null | undefined, decimals?: number) => string;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

const DEFAULT_INR_RATE = 95.67;

export const getLiveInrRate = (): number => {
  const cached = localStorage.getItem('usd_inr_rate');
  return cached ? parseFloat(cached) : DEFAULT_INR_RATE;
};

export const CurrencyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currency, setCurrencyState] = useState<Currency>(() => {
    return (localStorage.getItem('preferred_currency') as Currency) || 'USD';
  });
  const [exchangeRate, setExchangeRate] = useState<number>(() => getLiveInrRate());
  const [isRateLive, setIsRateLive] = useState<boolean>(false);

  useEffect(() => {
    const fetchLiveRate = async () => {
      try {
        const response = await fetch('https://open.er-api.com/v6/latest/USD');
        if (response.ok) {
          const data = await response.json();
          if (data?.rates?.INR) {
            const liveRate = data.rates.INR;
            setExchangeRate(liveRate);
            setIsRateLive(true);
            localStorage.setItem('usd_inr_rate', liveRate.toString());
          }
        }
      } catch (err) {
        console.warn('Failed to fetch live USD/INR exchange rate, using fallback rate:', err);
      }
    };

    fetchLiveRate();
  }, []);

  const setCurrency = (c: Currency) => {
    setCurrencyState(c);
    localStorage.setItem('preferred_currency', c);
  };

  const formatCost = (val: number | string | null | undefined, decimals = 2): string => {
    if (val === null || val === undefined) return currency === 'INR' ? '₹0.00' : '$0.00';
    const num = Number(val);
    if (isNaN(num)) return currency === 'INR' ? '₹0.00' : '$0.00';

    if (currency === 'INR') {
      const inrAmount = num * exchangeRate;
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

  return (
    <CurrencyContext.Provider
      value={{
        currency,
        exchangeRate,
        isRateLive,
        setCurrency,
        formatCost,
      }}
    >
      {children}
    </CurrencyContext.Provider>
  );
};

export const useCurrency = () => {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
};
