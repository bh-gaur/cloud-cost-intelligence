import { apiClient } from './client';

export interface SavingsOpportunity {
  id: string;
  title: string;
  category: string;
  service: string;
  estimated_monthly_savings: number;
  effort: string;
  risk: string;
  remediation_command?: string;
  description: string;
}

export interface AnomalyDiagnosis {
  service: string;
  detected_surge_pct: number;
  estimated_impact: number;
  root_cause_hypothesis: string;
  recommended_action: string;
}

export interface FinOpsInsights {
  health_score: number;
  total_monthly_spend: number;
  potential_monthly_savings: number;
  savings_percentage: number;
  executive_summary: string;
  top_opportunities: SavingsOpportunity[];
  anomalies: AnomalyDiagnosis[];
  quick_wins: string[];
  tagging_compliance_pct: number;
}

export interface CopilotChatResponse {
  reply: string;
  suggested_actions: string[];
  relevant_opportunities: SavingsOpportunity[];
  remediation_snippet?: string;
}

export const copilotApi = {
  getInsights: async (accountId: string = 'all'): Promise<FinOpsInsights> => {
    const res = await apiClient.get('/copilot/insights', {
      params: { account_id: accountId },
    });
    return res.data?.data;
  },

  chat: async (query: string, accountId: string = 'all'): Promise<CopilotChatResponse> => {
    const res = await apiClient.post('/copilot/chat', {
      query,
      account_id: accountId,
    });
    return res.data?.data;
  },
};
