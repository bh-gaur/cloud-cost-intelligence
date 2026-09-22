import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  TrendingDown,
  DollarSign,
  ShieldCheck,
  Zap,
  Sparkles,
  BarChart3,
  Layers,
  Building2,
  Bell,
  FileText,
  CheckCircle2,
  ArrowRight,
  ChevronRight,
  Lock,
  Cpu,
  Globe2,
  Calculator,
  Percent,
  TrendingUp,
  Award,
} from 'lucide-react';
import { ThemeToggle } from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';

export const Landing: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [demoLoading, setDemoLoading] = useState(false);

  // Interactive FinOps ROI Calculator State
  const [monthlySpend, setMonthlySpend] = useState<number>(50000);
  const [workloadType, setWorkloadType] = useState<'standard' | 'data' | 'hpc'>('data');

  // ROI Math calculations based on workload complexity
  const savingsPercent = workloadType === 'standard' ? 0.18 : workloadType === 'data' ? 0.24 : 0.32;
  const monthlySavings = monthlySpend * savingsPercent;
  const annualSavings = monthlySavings * 12;
  const estimatedRoiMultiple = (annualSavings / 9600).toFixed(1); // Baseline $800/mo SaaS tier

  const handleDemoAccess = async () => {
    setDemoLoading(true);
    try {
      localStorage.removeItem('active_org_id');
      await login({ email: 'admin@cloudcost.local', password: 'Admin123!@#' });
      navigate('/dashboard');
    } catch (err) {
      navigate('/login?demo=true');
    } finally {
      setDemoLoading(false);
    }
  };

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#09090b] dark:text-zinc-100 font-sans selection:bg-slate-300 dark:selection:bg-zinc-700 selection:text-slate-900 dark:selection:text-white relative overflow-hidden transition-colors duration-200">
      {/* Subtle Ambient Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-gradient-to-b from-slate-200/40 via-slate-100/10 dark:from-zinc-800/20 dark:via-zinc-900/10 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/90 border-b border-slate-200/80 dark:bg-[#09090b]/90 dark:border-zinc-800/80 shadow-sm transition-colors">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 dark:bg-[#141417] dark:border-zinc-800 p-2.5 flex items-center justify-center shadow-sm">
              <TrendingDown className="w-5 h-5 text-slate-800 dark:text-zinc-200" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                AWS Cost Intelligence
              </span>
              <span className="block text-[10px] font-semibold tracking-widest text-slate-500 dark:text-zinc-400 uppercase">
                Enterprise FinOps Platform
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600 dark:text-zinc-400">
            <button onClick={() => scrollToSection('features')} className="hover:text-slate-900 dark:hover:text-white transition-colors">
              Platform Features
            </button>
            <button onClick={() => scrollToSection('optimization')} className="hover:text-slate-900 dark:hover:text-white transition-colors">
              Optimization Engine
            </button>
            <button onClick={() => scrollToSection('architecture')} className="hover:text-slate-900 dark:hover:text-white transition-colors">
              Architecture & Security
            </button>
            <button onClick={() => scrollToSection('roi')} className="hover:text-slate-900 dark:hover:text-white transition-colors flex items-center gap-1 font-bold text-slate-700 dark:text-zinc-300">
              <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
              FinOps ROI
            </button>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <button
              onClick={() => navigate('/login')}
              className="text-sm font-semibold text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-white px-4 py-2 transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={handleDemoAccess}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-md transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              {demoLoading ? (
                <div className="w-4 h-4 border-2 border-white dark:!border-zinc-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Explore Demo</span>
                  <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="relative pt-20 pb-24 px-6 max-w-7xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-200/80 border border-slate-300 text-slate-800 dark:bg-zinc-800/80 dark:border-zinc-700 dark:text-zinc-300 text-xs font-semibold mb-8 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
          <span>Next-Generation Multi-Tenant FinOps Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-[1.15]">
          Master AWS Cloud Spend with{' '}
          <span className="bg-gradient-to-r from-slate-900 via-slate-700 to-slate-800 dark:from-zinc-100 dark:via-zinc-300 dark:to-zinc-400 bg-clip-text text-transparent">
            Precision Intelligence & Automation
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-zinc-400 max-w-2xl mx-auto leading-relaxed">
          Unify multi-account AWS spending, detect cost anomalies in real-time, execute 11+ automated optimization rules, and maintain 100% financial precision.
        </p>

        {/* CTA Button Row */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-lg transition-all hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3 cursor-pointer"
          >
            <span>Access Platform Console</span>
            <ChevronRight className="w-5 h-5 text-white dark:!text-zinc-950" />
          </button>

          <button
            onClick={handleDemoAccess}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-300 dark:text-white dark:bg-[#18181b] dark:hover:bg-zinc-800 dark:border-zinc-700 shadow-sm transition-all flex items-center justify-center gap-3 cursor-pointer"
          >
            <Sparkles className="w-5 h-5 text-amber-500" />
            <span>Launch Live Demo</span>
          </button>
        </div>

        {/* Key Platform Highlights Row */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
          <div className="p-4 rounded-xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm">
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100">100%</div>
            <div className="text-xs text-slate-500 dark:text-zinc-400 font-medium mt-1">Financial Precision (Decimal)</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm">
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100">11+</div>
            <div className="text-xs text-slate-500 dark:text-zinc-400 font-medium mt-1">Automated FinOps Rules</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm">
            <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100">Multi-Tenant</div>
            <div className="text-xs text-slate-500 dark:text-zinc-400 font-medium mt-1">Zero-Trust Isolation</div>
          </div>
          <div className="p-4 rounded-xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm">
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">Real-Time</div>
            <div className="text-xs text-slate-500 dark:text-zinc-400 font-medium mt-1">Anomaly Spike Alerts</div>
          </div>
        </div>

        {/* Dashboard Graphic Mockup Container */}
        <div className="mt-14 relative rounded-2xl p-2 bg-slate-200 border border-slate-300 dark:bg-[#141417] dark:border-zinc-800 shadow-2xl">
          <div className="bg-white border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800 rounded-xl overflow-hidden p-6 text-left">
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-200 dark:border-zinc-800">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                <span className="ml-3 text-xs font-mono text-slate-500 dark:text-zinc-400">
                  console.aws-cost-intelligence.internal • FinOps Scorecard
                </span>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                LIVE DEMO ENVIRONMENT
              </span>
            </div>

            {/* Mock KPI cards preview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#121215] dark:border-zinc-800">
                <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold uppercase tracking-wider">Today's AWS Spend</span>
                <div className="text-2xl font-bold text-slate-900 dark:text-white mt-1">$924.50</div>
                <div className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1 font-semibold">
                  <TrendingDown className="w-3.5 h-3.5" /> -4.2% vs. Yesterday
                </div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#121215] dark:border-zinc-800">
                <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold uppercase tracking-wider">Month-to-Date Spend</span>
                <div className="text-2xl font-bold text-slate-900 dark:text-zinc-100 mt-1">$27,186.95</div>
                <div className="text-xs text-slate-500 dark:text-zinc-400 mt-1 font-medium">Projected: $54,373.91</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#121215] dark:border-zinc-800">
                <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold uppercase tracking-wider">Potential Monthly Savings</span>
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">$6,713.65</div>
                <div className="text-xs text-emerald-600 dark:text-emerald-400/80 mt-1 font-semibold">11 Active Optimization Rules</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FINOPS ROI & INTERACTIVE CALCULATOR SECTION (ID: roi) */}
      <section id="roi" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-200 border border-slate-300 text-slate-800 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-300 text-xs font-semibold mb-4">
            <Calculator className="w-3.5 h-3.5 text-slate-700 dark:text-zinc-300" />
            <span>Interactive Business Impact Calculator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
            Calculate Your FinOps Cost Reduction & ROI
          </h2>
          <p className="mt-4 text-slate-600 dark:text-zinc-400 text-base">
            See how much your organization can save each month by eliminating idle EC2 compute, unattached EBS volumes, over-provisioned RDS, and untagged cloud waste.
          </p>
        </div>

        {/* Interactive Calculator Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          {/* Controls Column */}
          <div className="lg:col-span-6 p-7 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 space-y-6 shadow-xl flex flex-col justify-between">
            <div className="space-y-6">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-slate-700 dark:text-zinc-300" />
                Configure Cloud Parameters
              </h3>

              {/* Slider Input */}
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <label className="text-slate-700 dark:text-zinc-300 font-medium">Estimated Monthly AWS Spend</label>
                  <span className="text-slate-900 dark:text-white font-extrabold text-lg">${monthlySpend.toLocaleString()} / mo</span>
                </div>
                <input
                  type="range"
                  min={5000}
                  max={500000}
                  step={5000}
                  value={monthlySpend}
                  onChange={(e) => setMonthlySpend(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 dark:bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-slate-900 dark:accent-zinc-200"
                />
                <div className="flex justify-between text-[11px] text-slate-500 dark:text-zinc-500 font-mono">
                  <span>$5,000/mo</span>
                  <span>$250,000/mo</span>
                  <span>$500,000/mo</span>
                </div>
              </div>

              {/* Workload Selector */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider block">
                  AWS Workload & Infrastructure Profile
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setWorkloadType('standard')}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition-all ${workloadType === 'standard'
                      ? 'bg-slate-900 text-white border-slate-900 dark:!bg-white dark:!text-zinc-950 dark:!border-white shadow-md'
                      : 'bg-slate-100 text-slate-700 border-slate-200 hover:text-slate-900 dark:bg-[#09090b] dark:text-zinc-300 dark:border-zinc-800 dark:hover:text-white'
                      }`}
                  >
                    <span className="block font-bold">Standard Web</span>
                    <span className="text-[10px] opacity-80 mt-0.5">~18% Waste</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setWorkloadType('data')}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition-all ${workloadType === 'data'
                      ? 'bg-slate-900 text-white border-slate-900 dark:!bg-white dark:!text-zinc-950 dark:!border-white shadow-md'
                      : 'bg-slate-100 text-slate-700 border-slate-200 hover:text-slate-900 dark:bg-[#09090b] dark:text-zinc-300 dark:border-zinc-800 dark:hover:text-white'
                      }`}
                  >
                    <span className="block font-bold">Microservices</span>
                    <span className="text-[10px] opacity-80 mt-0.5">~24% Waste</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setWorkloadType('hpc')}
                    className={`p-3 rounded-xl border text-xs font-bold text-center transition-all ${workloadType === 'hpc'
                      ? 'bg-slate-900 text-white border-slate-900 dark:!bg-white dark:!text-zinc-950 dark:!border-white shadow-md'
                      : 'bg-slate-100 text-slate-700 border-slate-200 hover:text-slate-900 dark:bg-[#09090b] dark:text-zinc-300 dark:border-zinc-800 dark:hover:text-white'
                      }`}
                  >
                    <span className="block font-bold">Data & AI/ML</span>
                    <span className="text-[10px] opacity-80 mt-0.5">~32% Waste</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Itemized Waste Estimate */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800 space-y-2 text-xs">
              <div className="flex justify-between text-slate-600 dark:text-zinc-400">
                <span>EC2 Idle & Rightsizing Reduction:</span>
                <span className="font-bold text-slate-900 dark:text-white">${(monthlySavings * 0.45).toLocaleString('en-US', { maximumFractionDigits: 0 })}/mo</span>
              </div>
              <div className="flex justify-between text-slate-600 dark:text-zinc-400">
                <span>Unattached EBS Volume Cleanup:</span>
                <span className="font-bold text-slate-900 dark:text-white">${(monthlySavings * 0.25).toLocaleString('en-US', { maximumFractionDigits: 0 })}/mo</span>
              </div>
              <div className="flex justify-between text-slate-600 dark:text-zinc-400">
                <span>RDS Reserved Instances & S3 Transitions:</span>
                <span className="font-bold text-slate-900 dark:text-white">${(monthlySavings * 0.30).toLocaleString('en-US', { maximumFractionDigits: 0 })}/mo</span>
              </div>
            </div>
          </div>

          {/* Results Summary Column */}
          <div className="lg:col-span-6 p-7 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 shadow-2xl flex flex-col justify-between relative overflow-hidden">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400">
                  Estimated FinOps Savings Output
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <Award className="w-3.5 h-3.5" /> High ROI Impact
                </span>
              </div>

              {/* Monthly & Annual Metrics */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800">
                  <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold block mb-1">Identified Monthly Savings</span>
                  <div className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                    ${monthlySavings.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </div>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400/80 font-medium">~{(savingsPercent * 100).toFixed(0)}% cloud waste reduction</span>
                </div>

                <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800">
                  <span className="text-xs text-slate-500 dark:text-zinc-400 font-semibold block mb-1">Identified Annual Savings</span>
                  <div className="text-3xl font-extrabold text-slate-900 dark:text-white">
                    ${annualSavings.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                  </div>
                  <span className="text-[10px] text-slate-500 dark:text-zinc-400 font-medium">Direct bottom-line impact</span>
                </div>
              </div>

              {/* Projected ROI Banner */}
              <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 dark:bg-[#18181b] dark:border-zinc-700 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-600 dark:text-zinc-400 font-medium">Estimated Platform ROI</span>
                  <div className="text-2xl font-extrabold text-slate-900 dark:text-white mt-0.5">{estimatedRoiMultiple}x Return</div>
                </div>
                <button
                  onClick={handleDemoAccess}
                  className="px-4 py-2 text-xs font-bold text-white bg-slate-900 hover:bg-slate-800 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 rounded-lg shadow-md border border-slate-900 dark:!border-white transition-all cursor-pointer"
                >
                  Verify Your Savings →
                </button>
              </div>
            </div>

            <p className="text-[11px] text-slate-500 dark:text-zinc-500 mt-6 leading-normal">
              * Savings projections are based on empirical FinOps benchmarks across 11 automated rules evaluating EC2, EBS, RDS, S3, Data Transfer, and Reserved Instance utilization.
            </p>
          </div>
        </div>
      </section>

      {/* CORE CAPABILITIES / FEATURES SECTION */}
      <section id="features" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-zinc-400 mb-2">
            Complete FinOps Tooling
          </h2>
          <h3 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
            Built for Cloud Architects, Engineers & Finance Leaders
          </h3>
          <p className="mt-4 text-slate-600 dark:text-zinc-400 text-base">
            Everything required to analyze, optimize, and control enterprise AWS spend across accounts and regions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <BarChart3 className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Multi-Period Spend Analytics</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Track 7d, 14d, 30d, 90d, MTD and custom range spend with interactive line, bar, donut, and scatter visualizations.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Zap className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">11+ Automated Optimization Rules</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Instant detection of unattached EBS volumes, idle EC2 instances, over-provisioned RDS databases, and obsolete snapshots.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Bell className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Anomaly Spikes & Multi-Channel Alerts</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Detect sudden cost spikes with statistical thresholding and broadcast notifications to Slack, Email, PagerDuty, or Webhooks.
            </p>
          </div>

          {/* Card 4 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Building2 className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Enterprise Multi-Tenancy & RBAC</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Isolated organization boundaries, granular role permissions (OWNER, ADMIN, ANALYST), secure member invitations, and audit logs.
            </p>
          </div>

          {/* Card 5 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <Globe2 className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Multi-Account & Region Visibility</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Aggregate cost breakdowns across Payer/Linked accounts, global AWS regions, and specific service categories.
            </p>
          </div>

          {/* Card 6 */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Executive Reports & Exports</h4>
            <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
              Generate executive HTML scorecards and itemized CSV spend reports on demand or via scheduled recurring background jobs.
            </p>
          </div>
        </div>
      </section>

      {/* OPTIMIZATION ENGINE SECTION (ID: optimization) */}
      <section id="optimization" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-semibold mb-4">
              <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Automated Savings Detection</span>
            </div>
            <h3 className="text-3xl font-extrabold text-slate-900 dark:text-white leading-tight">
              Uncover 15% - 35% Inactive AWS Spend in Seconds
            </h3>
            <p className="mt-4 text-slate-600 dark:text-zinc-400 text-sm leading-relaxed">
              Our rule-based FinOps engine continuously scans your AWS cost records, identifying waste across EC2, EBS, RDS, S3, Data Transfer, and Elastic IPs.
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h5 className="text-sm font-bold text-slate-900 dark:text-white">Unattached EBS Volumes & Elastic IPs</h5>
                  <p className="text-xs text-slate-500 dark:text-zinc-400">Identifies unallocated block storage and unassigned static IP addresses incurring hourly fees.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h5 className="text-sm font-bold text-slate-900 dark:text-white">Idle & Right-sizing Candidates</h5>
                  <p className="text-xs text-slate-500 dark:text-zinc-400">Flags low CPU utilization compute instances and underutilized multi-AZ database deployments.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h5 className="text-sm font-bold text-slate-900 dark:text-white">S3 Storage Class & Lifecycle Transitions</h5>
                  <p className="text-xs text-slate-500 dark:text-zinc-400">Recommends automated movement of inactive objects to Glacier Instant Retrieval or Deep Archive.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 space-y-4 shadow-xl">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-zinc-800">
              <span className="text-xs font-bold text-slate-700 dark:text-zinc-300 uppercase tracking-wider">Sample Optimization Findings</span>
              <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold">$6,713.65 / mo Potential Savings</span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-rose-600 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">HIGH PRIORITY</span>
                <h5 className="text-xs font-bold text-slate-900 dark:text-white mt-1.5">Delete Unattached EBS Volume (vol-049fa821)</h5>
                <p className="text-[11px] text-slate-500 dark:text-zinc-400">us-east-1 • 500 GB gp3 unattached for 45 days</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">$60.00 / mo</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">MEDIUM PRIORITY</span>
                <h5 className="text-xs font-bold text-slate-900 dark:text-white mt-1.5">Right-size Idle EC2 Instance (i-0812ab34)</h5>
                <p className="text-[11px] text-slate-500 dark:text-zinc-400">us-west-2 • Average CPU utilization &lt; 3.2%</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">$184.20 / mo</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 dark:bg-[#09090b] dark:border-zinc-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-700 dark:text-zinc-300 bg-slate-200 dark:bg-zinc-800 px-2 py-0.5 rounded border border-slate-300 dark:border-zinc-700">OBSERVED WASTE</span>
                <h5 className="text-xs font-bold text-slate-900 dark:text-white mt-1.5">Release Unassigned Elastic IP (34.210.12.9)</h5>
                <p className="text-[11px] text-slate-500 dark:text-zinc-400">eu-west-1 • Unassociated for 12 days</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">$3.60 / mo</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ARCHITECTURE & SECURITY SECTION (ID: architecture) */}
      <section id="architecture" className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-zinc-400 mb-2">
            Enterprise Architecture
          </h2>
          <h3 className="text-3xl font-extrabold text-slate-900 dark:text-white">
            Production-Grade Security & Financial Standards
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 shadow-sm">
            <Lock className="w-8 h-8 text-slate-700 dark:text-zinc-300 mb-4" />
            <h4 className="text-base font-bold text-slate-900 dark:text-white mb-2">Tenant Isolation</h4>
            <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
              Every database query and API endpoint validates tenant ownership via <code className="text-slate-800 dark:text-zinc-200">TenantContext</code> middleware, enforcing total organization data separation.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 shadow-sm">
            <Cpu className="w-8 h-8 text-slate-700 dark:text-zinc-300 mb-4" />
            <h4 className="text-base font-bold text-slate-900 dark:text-white mb-2">100% Decimal Precision</h4>
            <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
              Zero floating-point rounding errors. Costs, variances, and savings are calculated using Python <code className="text-slate-800 dark:text-zinc-200">Decimal</code> and stored as high-precision numeric types.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 shadow-sm">
            <ShieldCheck className="w-8 h-8 text-slate-700 dark:text-zinc-300 mb-4" />
            <h4 className="text-base font-bold text-slate-900 dark:text-white mb-2">Role-Based Access Control</h4>
            <p className="text-xs text-slate-600 dark:text-zinc-400 leading-relaxed">
              Strict RBAC enforcement for OWNER, ADMIN, and USER roles with audit logging of administrative events and member role transitions.
            </p>
          </div>
        </div>
      </section>

      {/* BOTTOM CTA BANNER */}
      <section className="py-20 px-6 max-w-7xl mx-auto">
        <div className="rounded-3xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 p-10 sm:p-14 text-center relative overflow-hidden shadow-2xl">
          <h3 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
            Ready to Optimize Your AWS Cloud Infrastructure?
          </h3>
          <p className="mt-4 text-slate-600 dark:text-zinc-400 text-base max-w-2xl mx-auto">
            Sign in to access your organization's FinOps dashboard or launch the live demo environment to explore cost intelligence tools.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/login')}
              className="px-8 py-3.5 rounded-xl text-base font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-lg transition-all hover:scale-105 cursor-pointer"
            >
              Sign In to Platform
            </button>
            <button
              onClick={handleDemoAccess}
              className="px-8 py-3.5 rounded-xl text-base font-bold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-300 dark:text-white dark:bg-[#18181b] dark:hover:bg-zinc-800 dark:border-zinc-700 transition-all cursor-pointer"
            >
              Explore Live Demo Mode
            </button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-12 border-t border-slate-200 dark:border-zinc-800/80 text-xs text-slate-500 dark:text-zinc-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <TrendingDown className="w-4 h-4 text-slate-700 dark:text-zinc-300" />
            <span className="font-bold text-slate-800 dark:text-zinc-200">AWS Cost Intelligence</span>
            <span>© 2026 FinOps SaaS Platform</span>
          </div>

          <div className="flex items-center gap-6 text-slate-600 dark:text-zinc-400">
            <button onClick={() => scrollToSection('features')} className="hover:text-slate-900 dark:hover:text-white transition-colors">Features</button>
            <button onClick={() => scrollToSection('optimization')} className="hover:text-slate-900 dark:hover:text-white transition-colors">Optimization</button>
            <button onClick={() => scrollToSection('architecture')} className="hover:text-slate-900 dark:hover:text-white transition-colors">Security</button>
            <button onClick={() => scrollToSection('roi')} className="hover:text-slate-900 dark:hover:text-white transition-colors">ROI Calculator</button>
            <Link to="/login" className="hover:text-slate-900 dark:hover:text-white transition-colors">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
