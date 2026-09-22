import { apiClient } from './client';
import { ApiResponse, OrganizationMember, Organization } from '../types';

export const organizationApi = {
  getMyOrganizations: async () => {
    const res = await apiClient.get<ApiResponse<OrganizationMember[]>>('/organizations/me');
    return res.data;
  },

  createOrganization: async (data: { name: string; slug?: string }) => {
    const res = await apiClient.post<ApiResponse<Organization>>('/organizations', data);
    return res.data;
  },

  switchOrganization: async (organization_id: string) => {
    const res = await apiClient.post<ApiResponse<{ message: string; organization_id: string; role: string }>>(
      '/organizations/switch',
      { organization_id }
    );
    return res.data;
  },

  getMembers: async (organizationId: string) => {
    const res = await apiClient.get<ApiResponse<any[]>>(`/organizations/${organizationId}/members`);
    return res.data;
  },

  inviteMember: async (organizationId: string, data: { email: string; role: string }) => {
    const res = await apiClient.post<ApiResponse<any>>(`/organizations/${organizationId}/members/invite`, data);
    return res.data;
  },

  updateMember: async (organizationId: string, memberId: string, data: { role?: string; status?: string }) => {
    const res = await apiClient.patch<ApiResponse<any>>(`/organizations/${organizationId}/members/${memberId}`, data);
    return res.data;
  },

  removeMember: async (organizationId: string, memberId: string) => {
    const res = await apiClient.delete<ApiResponse<any>>(`/organizations/${organizationId}/members/${memberId}`);
    return res.data;
  },

  getInvitations: async (organizationId: string) => {
    const res = await apiClient.get<ApiResponse<any[]>>(`/organizations/${organizationId}/invitations`);
    return res.data;
  },

  cancelInvitation: async (organizationId: string, invitationId: string) => {
    const res = await apiClient.delete<ApiResponse<any>>(`/organizations/${organizationId}/invitations/${invitationId}`);
    return res.data;
  },

  getInviteDetails: async (token: string) => {
    const res = await apiClient.get<ApiResponse<any>>(`/auth/invite-details?token=${encodeURIComponent(token)}`);
    return res.data;
  },

  acceptInvite: async (token: string) => {
    const res = await apiClient.post<ApiResponse<any>>('/auth/accept-invite', { token });
    return res.data;
  },

  acceptInviteAndRegister: async (data: { token: string; full_name: string; password: string }) => {
    const res = await apiClient.post<ApiResponse<any>>('/auth/accept-invite-register', data);
    return res.data;
  },
};
