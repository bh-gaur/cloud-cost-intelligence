import { apiClient } from './client';
import { ApiResponse } from '../types';

export interface UntaggedResource {
  resource_id: string;
  resource_name: string;
  service: string;
  resource_type: string;
  region: string;
  account_id: string;
  missing_tags: string[];
  existing_tags: Record<string, string>;
  monthly_spend: number | string;
  compliance_score: number;
  cli_remediation: string;
  terraform_remediation: string;
}

export interface ServiceTagCompliance {
  service: string;
  total_resources: number;
  tagged_resources: number;
  untagged_resources: number;
  compliance_percentage: number | string;
  untagged_spend: number | string;
}

export interface TagGovernanceResponse {
  overall_compliance_percentage: number | string;
  total_spend: number | string;
  tagged_spend: number | string;
  untagged_spend: number | string;
  total_resources: number;
  untagged_resources_count: number;
  required_tags: string[];
  service_breakdowns: ServiceTagCompliance[];
  missing_by_tag_key: Record<string, number>;
  resources: UntaggedResource[];
}

export interface RemediationGenerateRequest {
  resource_id: string;
  service: string;
  region: string;
  resource_type: string;
  custom_tags: Record<string, string>;
}

export interface RemediationGenerateResponse {
  resource_id: string;
  cli_command: string;
  terraform_snippet: string;
}

export const taggingApi = {
  getGovernance: (accountId: string = 'all') =>
    apiClient
      .get<ApiResponse<TagGovernanceResponse>>('/tagging/governance', {
        params: { account_id: accountId },
      })
      .then((res) => res.data),

  generateRemediation: (data: RemediationGenerateRequest) =>
    apiClient
      .post<ApiResponse<RemediationGenerateResponse>>('/tagging/remediation', data)
      .then((res) => res.data),
};
