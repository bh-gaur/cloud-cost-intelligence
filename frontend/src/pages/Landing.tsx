import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
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

  // Always reset scroll to the very top on reload / page entry
  useEffect(() => {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' as ScrollBehavior });
  }, []);

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
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-[#09090b] dark:text-zinc-100 font-sans selection:bg-slate-300 dark:selection:bg-zinc-700 selection:text-slate-900 dark:selection:text-white relative overflow-x-clip transition-colors duration-200">
      {/* Subtle Ambient Glow */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
        className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[550px] bg-gradient-to-b from-sky-400/15 via-blue-500/10 dark:from-sky-500/10 dark:via-blue-600/5 to-transparent blur-3xl pointer-events-none -z-10"
      />

      {/* Navigation Header */}
      <motion.header
        initial={{ y: -25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        className="sticky top-0 z-50 w-full backdrop-blur-xl bg-white/90 border-b border-slate-200/80 dark:bg-[#09090b]/90 dark:border-zinc-800/80 shadow-sm transition-colors"
      >
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <motion.div
              whileHover={{ rotate: [0, -10, 10, 0] }}
              transition={{ duration: 0.5 }}
              className="w-10 h-10 rounded-xl bg-slate-100 border border-slate-200 dark:bg-[#141417] dark:border-zinc-800 p-2.5 flex items-center justify-center shadow-sm"
            >
              <TrendingDown className="w-5 h-5 text-slate-800 dark:text-zinc-200" />
            </motion.div>
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
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleDemoAccess}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-md transition-all cursor-pointer"
            >
              {demoLoading ? (
                <div className="w-4 h-4 border-2 border-white dark:!border-zinc-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <span>Explore Demo</span>
                  <ArrowRight className="w-4 h-4 text-white dark:!text-zinc-950" />
                </>
              )}
            </motion.button>
          </div>
        </div>
      </motion.header>

      {/* HERO SECTION */}
      <section className="relative pt-20 pb-24 px-6 max-w-7xl mx-auto text-center">
        {/* Animated Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.88, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-200/80 border border-slate-300 text-slate-800 dark:bg-zinc-800/80 dark:border-zinc-700 dark:text-zinc-300 text-xs font-semibold mb-8 shadow-sm"
        >
          <Sparkles className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
          <span>Next-Generation Multi-Tenant FinOps Platform</span>
        </motion.div>

        {/* Animated Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 25 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white max-w-4xl mx-auto leading-[1.15]"
        >
          Master AWS Cloud Spend with{' '}
          <span className="bg-gradient-to-r from-slate-900 via-slate-700 to-slate-800 dark:from-zinc-100 dark:via-zinc-300 dark:to-zinc-400 bg-clip-text text-transparent">
            Precision Intelligence & Automation
          </span>
        </motion.h1>

        {/* Animated Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-zinc-400 max-w-2xl mx-auto leading-relaxed"
        >
          Unify multi-account AWS spending, detect cost anomalies in real-time, execute 11+ automated optimization rules, and maintain 100% financial precision.
        </motion.p>

        {/* CTA Button Row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate('/login')}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-lg transition-all flex items-center justify-center gap-3 cursor-pointer"
          >
            <span>Access Platform Console</span>
            <ChevronRight className="w-5 h-5 text-white dark:!text-zinc-950" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleDemoAccess}
            className="w-full sm:w-auto px-8 py-4 rounded-xl text-base font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-300 dark:text-white dark:bg-[#18181b] dark:hover:bg-zinc-800 dark:border-zinc-700 shadow-sm transition-all flex items-center justify-center gap-3 cursor-pointer"
          >
            <Sparkles className="w-5 h-5 text-amber-500" />
            <span>Launch Live Demo</span>
          </motion.button>
        </motion.div>

        {/* Key Platform Highlights Row */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
          {[
            { metric: '100%', label: 'Financial Precision (Decimal)', color: 'text-slate-900 dark:text-zinc-100' },
            { metric: '11+', label: 'Automated FinOps Rules', color: 'text-slate-900 dark:text-zinc-100' },
            { metric: 'Multi-Tenant', label: 'Zero-Trust Isolation', color: 'text-slate-900 dark:text-zinc-100' },
            { metric: 'Real-Time', label: 'Anomaly Spike Alerts', color: 'text-emerald-600 dark:text-emerald-400' },
          ].map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 22, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              transition={{ duration: 0.5, delay: 0.55 + index * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="p-4 rounded-xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className={`text-2xl font-bold ${item.color}`}>{item.metric}</div>
              <div className="text-xs text-slate-500 dark:text-zinc-400 font-medium mt-1">{item.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Dashboard Graphic Mockup Container */}
        <motion.div
          initial={{ opacity: 0, y: 35, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.75, ease: [0.16, 1, 0.3, 1] }}
          className="mt-14 relative rounded-2xl p-2 bg-slate-200 border border-slate-300 dark:bg-[#141417] dark:border-zinc-800 shadow-2xl"
        >
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
        </motion.div>
      </section>

      {/* FINOPS ROI & INTERACTIVE CALCULATOR SECTION (ID: roi) */}
      <motion.section
        id="roi"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20"
      >
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
      </motion.section>

      {/* CORE CAPABILITIES / FEATURES SECTION */}
      <motion.section
        id="features"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20"
      >
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
          {[
            {
              icon: <BarChart3 className="w-6 h-6" />,
              title: "Multi-Period Spend Analytics",
              description: "Track 7d, 14d, 30d, 90d, MTD and custom range spend with interactive line, bar, donut, and scatter visualizations."
            },
            {
              icon: <Zap className="w-6 h-6" />,
              title: "11+ Automated Optimization Rules",
              description: "Instant detection of unattached EBS volumes, idle EC2 instances, over-provisioned RDS databases, and obsolete snapshots."
            },
            {
              icon: <Bell className="w-6 h-6" />,
              title: "Anomaly Spikes & Multi-Channel Alerts",
              description: "Detect sudden cost spikes with statistical thresholding and broadcast notifications to Slack, Email, PagerDuty, or Webhooks."
            },
            {
              icon: <Building2 className="w-6 h-6" />,
              title: "Enterprise Multi-Tenancy & RBAC",
              description: "Isolated organization boundaries, granular role permissions (OWNER, ADMIN, ANALYST), secure member invitations, and audit logs."
            },
            {
              icon: <Globe2 className="w-6 h-6" />,
              title: "Multi-Account & Region Visibility",
              description: "Aggregate cost breakdowns across Payer/Linked accounts, global AWS regions, and specific service categories."
            },
            {
              icon: <FileText className="w-6 h-6" />,
              title: "Executive Reports & Exports",
              description: "Generate executive HTML scorecards and itemized CSV spend reports on demand or via scheduled recurring background jobs."
            }
          ].map((feature, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -6, scale: 1.01 }}
              transition={{ duration: 0.25 }}
              className="p-6 rounded-2xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800/90 shadow-sm hover:border-slate-300 dark:hover:border-zinc-700 transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-slate-100 border border-slate-200 dark:bg-zinc-800 dark:border-zinc-700 text-slate-800 dark:text-zinc-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                {feature.icon}
              </div>
              <h4 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{feature.title}</h4>
              <p className="text-sm text-slate-600 dark:text-zinc-400 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* OPTIMIZATION ENGINE SECTION (ID: optimization) */}
      <motion.section
        id="optimization"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20"
      >
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
      </motion.section>

      {/* ARCHITECTURE & SECURITY SECTION (ID: architecture) */}
      <motion.section
        id="architecture"
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="py-20 px-6 max-w-7xl mx-auto border-t border-slate-200 dark:border-zinc-800/80 scroll-mt-20"
      >
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
      </motion.section>

      {/* BOTTOM CTA BANNER */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="py-20 px-6 max-w-7xl mx-auto"
      >
        <div className="rounded-3xl bg-white border border-slate-200 dark:bg-[#121215] dark:border-zinc-800 p-10 sm:p-14 text-center relative overflow-hidden shadow-2xl">
          <h3 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white">
            Ready to Optimize Your AWS Cloud Infrastructure?
          </h3>
          <p className="mt-4 text-slate-600 dark:text-zinc-400 text-base max-w-2xl mx-auto">
            Sign in to access your organization's FinOps dashboard or launch the live demo environment to explore cost intelligence tools.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <motion.button
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => navigate('/login')}
              className="px-8 py-3.5 rounded-xl text-base font-bold text-white bg-slate-900 hover:bg-slate-800 border border-slate-900 dark:!text-zinc-950 dark:!bg-white dark:hover:!bg-zinc-100 dark:!border-white shadow-lg transition-all cursor-pointer"
            >
              Sign In to Platform
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.96 }}
              onClick={handleDemoAccess}
              className="px-8 py-3.5 rounded-xl text-base font-bold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-300 dark:text-white dark:bg-[#18181b] dark:hover:bg-zinc-800 dark:border-zinc-700 transition-all cursor-pointer"
            >
              Explore Live Demo Mode
            </motion.button>
          </div>
        </div>
      </motion.section>

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
