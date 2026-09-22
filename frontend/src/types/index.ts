export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  } | null;
  meta: {
    timestamp: string;
    version: string;
    demo_mode: boolean;
    page?: number;
    page_size?: number;
    total_count?: number;
    total_pages?: number;
  };
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  max_aws_accounts: number;
  created_at: string;
}

export type TenantRole = 'OWNER' | 'ADMIN' | 'FINOPS_MANAGER' | 'ANALYST' | 'VIEWER';

export interface OrganizationMember {
  id: string;
  organization_id: string;
  organization_name?: string;
  organization_slug?: string;
  user_id: string;
  email?: string;
  full_name?: string;
  role: TenantRole;
  status?: string;
  is_default?: boolean;
  joined_at?: string;
  created_at?: string;
}

export interface OrganizationInvitation {
  id: string;
  organization_id: string;
  email: string;
  role: TenantRole;
  status: 'PENDING' | 'ACCEPTED' | 'EXPIRED' | 'REVOKED';
  invitation_link: string;
  expires_at: string;
  created_at: string;
}

export interface InviteDetails {
  id: string;
  organization_id: string;
  organization_name: string;
  email: string;
  role: TenantRole;
  status: string;
  is_expired: boolean;
  user_exists?: boolean;
  expires_at: string | null;
}


export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'ADMIN' | 'USER';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface CostComparison {
  current_amount: number;
  previous_amount: number;
  difference: number;
  percentage_change: number;
  direction: 'UP' | 'DOWN' | 'FLAT';
}

export interface DashboardSummary {
  today_cost: number;
  yesterday_cost: number;
  previous_day_cost: number;
  today_date?: string;
  yesterday_date?: string;
  previous_day_date?: string;
  today_vs_yesterday: CostComparison;
  yesterday_vs_previous_day: CostComparison;
  currency: string;
  last_sync_at: string;
  data_freshness: string;
  account_context: string;
  region_context: string;
  is_demo_data: boolean;
}

export interface FinOpsKpis {
  total_monthly_spend: number;
  month_to_date_spend: number;
  projected_month_end_spend: number;
  potential_monthly_savings: number;
  potential_annual_savings: number;
  untagged_spend: number;
  untagged_percentage: number;
  budget_utilization: number;
  top_service: string;
  top_account: string;
  top_region: string;
  anomalies_detected: number;
}

export interface CostTrendPoint {
  date: string;
  total_cost: number;
  services: Record<string, number>;
}

export interface CostTrendResponse {
  range_label: string;
  chart_type: string;
  points: CostTrendPoint[];
  service_totals: Record<string, number>;
}

export interface CostRecord {
  id: string;
  provider: string;
  date: string;
  account_id: string;
  account_name: string;
  region: string;
  service: string;
  service_category: string;
  resource_id?: string;
  usage_quantity: number;
  usage_unit: string;
  cost: number;
  currency: string;
  tags: Record<string, string>;
  created_at: string;
}

export interface ServiceBreakdownItem {
  service: string;
  category: string;
  current_cost: number;
  percentage_of_total: number;
  previous_cost: number;
  difference: number;
  percentage_change: number;
  trend: 'UP' | 'DOWN' | 'FLAT';
}

export interface AccountBreakdownItem {
  account_id: string;
  account_name: string;
  monthly_cost: number;
  daily_cost: number;
  difference: number;
  percentage_of_total: number;
  trend: string;
}

export interface RegionBreakdownItem {
  region: string;
  cost: number;
  percentage_of_total: number;
  difference: number;
  trend: string;
}

export interface TagAnalysis {
  tagged_cost: number;
  untagged_cost: number;
  tagging_coverage_percentage: number;
  by_environment: Record<string, number>;
  by_team: Record<string, number>;
  by_application: Record<string, number>;
  by_project: Record<string, number>;
}

export interface OptimizationRecommendation {
  id: string;
  rule_id: string;
  rule_name: string;
  account_id: string;
  region: string;
  service: string;
  resource_id: string;
  resource_name?: string;
  current_monthly_cost: number;
  estimated_monthly_savings: number;
  estimated_annual_savings: number;
  savings_percentage: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: 'Observed' | 'Estimated' | 'Potential';
  validation_status: 'Requires validation' | 'Insufficient data' | 'Validated' | 'Dismissed';
  reason: string;
  recommendation: string;
  action_required: string;
  remediation_code?: string;
  implementation_effort?: 'LOW' | 'MEDIUM' | 'HIGH';
  operational_risk?: 'LOW' | 'MEDIUM' | 'HIGH';
  production_safety_score?: number;
  created_at: string;
}

export interface PotentialSavingsSummary {
  total_monthly_savings: number;
  total_annual_savings: number;
  by_priority: Record<string, number>;
  by_confidence: Record<string, number>;
  by_service: Record<string, number>;
  total_recommendations: number;
}

export interface ReportItem {
  id: string;
  name: string;
  format: 'csv' | 'json' | 'html' | 'pdf';
  start_date: string;
  end_date: string;
  account_id: string;
  file_size_bytes: number;
  status: string;
  created_by?: string;
  created_at: string;
  download_url: string;
}

export interface AnomalyEvent {
  id: string;
  title: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  account_id: string;
  service?: string;
  detected_value: number;
  expected_value?: number;
  difference_percentage?: number;
  message: string;
  status: string;
  created_at: string;
}

export interface BudgetRecord {
  id: string;
  budget_name: string;
  account_id: string;
  budget_limit: number;
  current_spend: number;
  forecasted_spend: number;
  remaining_budget: number;
  percentage_consumed: number;
  status: 'Healthy' | 'Warning' | 'Critical' | 'Exceeded';
  currency: string;
  period_start: string;
  period_end: string;
  updated_at: string;
}

export interface AlertSummary {
  active_anomalies: number;
  critical_anomalies: number;
  total_budgets: number;
  budgets_exceeded: number;
}

export interface CostAnomaly {
  id: number;
  account_id: string;
  service_name: string;
  anomaly_date: string;
  expected_cost: number;
  actual_cost: number;
  deviation_amount?: number;
  deviation_percentage?: number;
  severity: string;
  status: string;
  created_at: string;
}

export interface BudgetComparison {
  account_id: string;
  budget_name: string;
  budget_type: string;
  budgeted_amount: number;
  actual_spend: number;
  forecasted_spend: number;
  currency: string;
  status: string;
}

export interface ReportMetadata {
  id: number;
  report_name: string;
  report_type: string;
  format: 'csv' | 'json' | 'html' | 'pdf';
  file_path: string;
  file_size_bytes?: number;
  start_date: string;
  end_date: string;
  created_at: string;
  status: string;
}

export interface ReportGenerateRequest {
  report_type: string;
  format: 'csv' | 'json' | 'html' | 'pdf';
  start_date: string;
  end_date: string;
  account_id?: string;
  service?: string;
}
