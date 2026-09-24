import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Sparkles,
  Bot,
  Send,
  X,
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  ChevronRight,
  ShieldCheck,
  DollarSign,
  Terminal,
  RefreshCw,
  HelpCircle,
} from 'lucide-react';
import { copilotApi, FinOpsInsights, CopilotChatResponse } from '../api/copilotApi';
import { useCurrency } from '../context/CurrencyContext';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  suggestedActions?: string[];
  remediationSnippet?: string;
}

interface FinOpsCopilotProps {
  selectedAccount?: string;
}

export const FinOpsCopilot: React.FC<FinOpsCopilotProps> = ({ selectedAccount = 'all' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [inputQuery, setInputQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const { formatCost } = useCurrency();

  // Load FinOps Insights
  const { data: insights, isLoading: loadingInsights, refetch: refetchInsights } = useQuery<FinOpsInsights>({
    queryKey: ['copilotInsights', selectedAccount],
    queryFn: () => copilotApi.getInsights(selectedAccount),
    staleTime: 1000 * 60 * 5,
  });

  // Initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          sender: 'assistant',
          text: `👋 **Welcome to your FinOps AI Copilot!**\n\nI continuously monitor your AWS infrastructure to identify wasted spend, cost anomalies, and right-sizing opportunities.\n\nChoose a quick action below or ask me any question about your cloud budget.`,
          timestamp: new Date(),
          suggestedActions: ['⚡ Find Quick Wins', '📈 Explain Anomalies', '💰 Cut 20% Spend', '📋 Executive Brief'],
        },
      ]);
    }
  }, []);

  // Scroll to bottom when messages update
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [messages, isOpen]);

  // Chat Mutation
  const chatMutation = useMutation({
    mutationFn: (query: string) => copilotApi.chat(query, selectedAccount),
    onSuccess: (data: CopilotChatResponse) => {
      const assistantMsg: Message = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: data.reply,
        timestamp: new Date(),
        suggestedActions: data.suggested_actions,
        remediationSnippet: data.remediation_snippet,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    },
    onError: () => {
      const errorMsg: Message = {
        id: Math.random().toString(),
        sender: 'assistant',
        text: '⚠️ Unable to process query at this moment. Please check network connectivity.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    },
  });

  const handleSendMessage = (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || chatMutation.isPending) return;

    const userMsg: Message = {
      id: Math.random().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    chatMutation.mutate(query);
  };

  const handleCopySnippet = (snippet: string, key: string) => {
    navigator.clipboard.writeText(snippet);
    setCopiedIndex(key);
    setTimeout(() => setCopiedIndex(null), 2500);
  };

  return (
    <>
      {/* Floating Trigger Button */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-sky-600 via-indigo-600 to-purple-600 text-white font-medium shadow-[0_4px_25px_rgba(79,70,229,0.4)] hover:shadow-[0_6px_30px_rgba(79,70,229,0.55)] transition-all border border-white/20 backdrop-blur-md group"
      >
        <div className="relative">
          <Sparkles className="w-5 h-5 text-amber-300 animate-pulse" />
          <span className="absolute -top-1 -right-1 flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
        </div>
        <span className="text-sm font-semibold tracking-wide">FinOps Copilot</span>
        {insights?.potential_monthly_savings && insights.potential_monthly_savings > 0 && (
          <span className="hidden sm:inline-block text-xs bg-emerald-500/25 border border-emerald-400/40 text-emerald-200 px-2 py-0.5 rounded-full">
            Save {formatCost(insights.potential_monthly_savings)}/mo
          </span>
        )}
      </motion.button>

      {/* Copilot Drawer / Modal */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, x: 400 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 400 }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              className="w-full max-w-lg h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col justify-between text-slate-100 overflow-hidden"
            >
              {/* Header */}
              <div className="p-4 border-b border-slate-800 bg-slate-900/90 backdrop-blur flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 text-white shadow-md">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white flex items-center gap-1.5">
                      FinOps AI Advisor
                      <span className="text-[10px] font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30 px-1.5 py-0.5 rounded">
                        v1.0 AI
                      </span>
                    </h3>
                    <p className="text-xs text-slate-400">Autonomous AWS Cost & Anomaly Intelligence</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => refetchInsights()}
                    title="Refresh telemetry"
                    className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <RefreshCw className={`w-4 h-4 ${loadingInsights ? 'animate-spin text-sky-400' : ''}`} />
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* KPI Banner */}
              {insights && (
                <div className="p-3 bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950/40 border-b border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                    <p className="text-[11px] text-slate-400 font-medium">Efficiency Score</p>
                    <p className="text-sm font-bold text-emerald-400 mt-0.5">{insights.health_score}/100</p>
                  </div>
                  <div className="p-2 rounded-lg bg-slate-800/50 border border-slate-700/50">
                    <p className="text-[11px] text-slate-400 font-medium">Monthly Spend</p>
                    <p className="text-sm font-bold text-slate-200 mt-0.5">
                      {formatCost(insights.total_monthly_spend)}
                    </p>
                  </div>
                  <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/40">
                    <p className="text-[11px] text-emerald-300 font-medium">Reclaimable</p>
                    <p className="text-sm font-bold text-emerald-400 mt-0.5">
                      {formatCost(insights.potential_monthly_savings)}
                    </p>
                  </div>
                </div>
              )}

              {/* Chat Message Stream */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-sm">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[88%] rounded-2xl p-3.5 shadow-sm leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-gradient-to-r from-sky-600 to-blue-600 text-white rounded-br-none'
                          : 'bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none'
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{msg.text}</div>

                      {/* Remediation Snippet Block */}
                      {msg.remediationSnippet && (
                        <div className="mt-3 rounded-lg bg-slate-950 border border-slate-800 p-2.5 font-mono text-xs text-sky-300 relative group/code">
                          <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-slate-800 text-[10px] text-slate-400">
                            <span className="flex items-center gap-1">
                              <Terminal className="w-3 h-3 text-emerald-400" /> AWS CLI / Fix Snippet
                            </span>
                            <button
                              onClick={() => handleCopySnippet(msg.remediationSnippet!, msg.id)}
                              className="flex items-center gap-1 hover:text-white transition-colors"
                            >
                              {copiedIndex === msg.id ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-400" /> Copied
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" /> Copy
                                </>
                              )}
                            </button>
                          </div>
                          <pre className="overflow-x-auto select-all">{msg.remediationSnippet}</pre>
                        </div>
                      )}
                    </div>

                    {/* Quick Suggestion Chips */}
                    {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2 max-w-[90%]">
                        {msg.suggestedActions.map((action, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(action)}
                            className="text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 border border-sky-500/30 px-2.5 py-1 rounded-full transition-colors flex items-center gap-1 font-medium"
                          >
                            <ChevronRight className="w-3 h-3" /> {action}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {chatMutation.isPending && (
                  <div className="flex items-center gap-2 text-xs text-slate-400 italic">
                    <div className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
                    FinOps Copilot is analyzing telemetry & rules...
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Input Box */}
              <div className="p-3 border-t border-slate-800 bg-slate-900/90 backdrop-blur">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inputQuery}
                    onChange={(e) => setInputQuery(e.target.value)}
                    placeholder="Ask FinOps AI: 'Where can we save 20%?' or 'Explain EC2 spike'..."
                    className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
                  />
                  <button
                    type="submit"
                    disabled={!inputQuery.trim() || chatMutation.isPending}
                    className="p-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
