import React, { useState, useEffect } from 'react';
import {
  Users,
  CheckCircle2,
  XCircle,
  Search,
  UserPlus,
  X,
  AlertCircle,
  Copy,
  Check,
  Mail,
  Shield,
  Clock,
  Trash2,
  Building2,
  RefreshCw,
} from 'lucide-react';
import { adminApi } from '../api/adminApi';
import { organizationApi } from '../api/organizationApi';
import { useAuth } from '../context/AuthContext';
import { LoadingSkeleton } from '../components/LoadingSkeleton';
import { ConfirmModal } from '../components/ConfirmModal';
import type { User, OrganizationMember, OrganizationInvitation, TenantRole } from '../types';

export const AdminUsers: React.FC = () => {
  const { activeOrgId, activeOrg, refetchOrganizations } = useAuth();
  const canManageMembers = activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN' || activeOrg?.role === 'FINOPS_MANAGER';

  const [activeTab, setActiveTab] = useState<'members' | 'invitations' | 'all'>('members');

  const [users, setUsers] = useState<User[]>([]);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);

  const pendingCount = invitations.filter((i) => i.status === 'PENDING').length;

  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const handleRoleChange = async (memberId: string, newRole: TenantRole) => {
    if (!activeOrgId) return;
    try {
      setUpdatingMemberId(memberId);
      const res = await organizationApi.updateMember(activeOrgId, memberId, { role: newRole });
      if (res.success || (res as any)?.status === 'SUCCESS' || res.data) {
        setMembers((prev) =>
          prev.map((m) => (m.id === memberId ? { ...m, role: newRole } : m))
        );
        await refetchOrganizations();
      }
    } catch (err: any) {
      console.error('Failed to update member role:', err);
      alert(err.response?.data?.error?.message || 'Failed to update member role.');
    } finally {
      setUpdatingMemberId(null);
    }
  };

  // Confirmation Modals State
  const [memberToDelete, setMemberToDelete] = useState<OrganizationMember | null>(null);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [inviteToRevoke, setInviteToRevoke] = useState<OrganizationInvitation | null>(null);
  const [isDeletingMember, setIsDeletingMember] = useState(false);
  const [isDeletingUser, setIsDeletingUser] = useState(false);
  const [isRevokingInvite, setIsRevokingInvite] = useState(false);

  // Invite Modal State
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('ANALYST');
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState<string | null>(null);
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  const fetchAllData = async () => {
    try {
      setLoading(true);

      const [usersRes, membersRes, invitesRes] = await Promise.allSettled([
        adminApi.getUsers(),
        activeOrgId ? organizationApi.getMembers(activeOrgId) : Promise.resolve(null),
        activeOrgId ? organizationApi.getInvitations(activeOrgId) : Promise.resolve(null),
      ]);

      if (usersRes.status === 'fulfilled' && usersRes.value?.success && usersRes.value?.data) {
        setUsers(usersRes.value.data);
      }

      if (membersRes.status === 'fulfilled' && membersRes.value?.success && membersRes.value?.data) {
        setMembers(membersRes.value.data);
      }

      if (invitesRes.status === 'fulfilled' && invitesRes.value?.success && invitesRes.value?.data) {
        setInvitations(invitesRes.value.data);
      }
    } catch (err) {
      console.error('Failed to load user and team data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [activeOrgId]);

  const handleInviteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError(null);
    setInviteSuccess(null);
    setInviteLink(null);

    if (!inviteEmail) {
      setInviteError('Please enter a valid email address.');
      return;
    }
    if (!activeOrgId) {
      setInviteError('No active organization selected.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await organizationApi.inviteMember(activeOrgId, {
        email: inviteEmail.trim(),
        role: inviteRole,
      });

      if (res.success && res.data) {
        setInviteSuccess(`Invitation successfully generated for ${inviteEmail}!`);
        const fullLink = `${window.location.origin}${res.data.invitation_link}`;
        setInviteLink(fullLink);
        await fetchAllData();
      }
    } catch (err: any) {
      setInviteError(err.response?.data?.error?.message || err.message || 'Failed to send invitation.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(id);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  const confirmRevokeInvite = async () => {
    if (!activeOrgId || !inviteToRevoke) return;
    try {
      setIsRevokingInvite(true);
      const res = await organizationApi.cancelInvitation(activeOrgId, inviteToRevoke.id);
      if (res.success) {
        setInvitations((prev) => prev.filter((i) => i.id !== inviteToRevoke.id));
        setInviteToRevoke(null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to revoke invitation.');
    } finally {
      setIsRevokingInvite(false);
    }
  };

  const confirmRemoveMember = async () => {
    if (!activeOrgId || !memberToDelete) return;
    try {
      setIsDeletingMember(true);
      const res = await organizationApi.removeMember(activeOrgId, memberToDelete.id);
      if (res.success) {
        const deletedEmail = memberToDelete.email?.toLowerCase();
        setMembers((prev) => prev.filter((m) => m.id !== memberToDelete.id));
        if (deletedEmail) {
          setUsers((prev) => prev.filter((u) => u.email.toLowerCase() !== deletedEmail));
        }
        setMemberToDelete(null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to remove member.');
    } finally {
      setIsDeletingMember(false);
    }
  };

  const confirmDeleteUser = async () => {
    if (!userToDelete) return;
    try {
      setIsDeletingUser(true);
      const res = await adminApi.deleteUser(userToDelete.id);
      if (res.success) {
        const deletedId = userToDelete.id;
        const deletedEmail = userToDelete.email.toLowerCase();
        setUsers((prev) => prev.filter((u) => u.id !== deletedId));
        setMembers((prev) => prev.filter((m) => m.user_id !== deletedId && m.email?.toLowerCase() !== deletedEmail));
        setUserToDelete(null);
      }
    } catch (err: any) {
      alert(err.response?.data?.error?.message || 'Failed to delete user.');
    } finally {
      setIsDeletingUser(false);
    }
  };

  const copyInviteLink = (link: string, id: string) => {
    navigator.clipboard.writeText(link);
    setCopiedToken(id);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  const filteredMembers = members.filter(
    (m) =>
      m.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      m.email?.toLowerCase().includes(search.toLowerCase()) ||
      m.role?.toLowerCase().includes(search.toLowerCase())
  );

  const filteredInvitations = invitations.filter(
    (inv) =>
      inv.email?.toLowerCase().includes(search.toLowerCase()) ||
      inv.role?.toLowerCase().includes(search.toLowerCase()) ||
      inv.status?.toLowerCase().includes(search.toLowerCase())
  );

  const filteredUsers = users.filter(
    (u) =>
      u.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      u.role?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Team & User Management</h1>
            <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-300 dark:border-blue-800">
              Admin Exclusive
            </span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Invite team members, configure role permissions (RBAC), and manage organization access.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search team or directory..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-64 shadow-2xs"
            />
          </div>

          {canManageMembers && (
            <button
              onClick={() => {
                setIsInviteOpen(true);
                setInviteError(null);
                setInviteSuccess(null);
                setInviteLink(null);
                setInviteEmail('');
              }}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 rounded-xl shadow-xs transition-all cursor-pointer shrink-0"
            >
              <UserPlus className="w-4 h-4" />
              <span>Invite User</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('members')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 cursor-pointer ${
            activeTab === 'members'
              ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Building2 className="w-4 h-4" />
          <span>Organization Members ({members.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('invitations')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 cursor-pointer ${
            activeTab === 'invitations'
              ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Pending Invitations</span>
          {pendingCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-bold">
              {pendingCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-colors flex items-center gap-2 cursor-pointer ${
            activeTab === 'all'
              ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Platform Directory ({users.length})</span>
        </button>
      </div>

      {/* Tab 1: Organization Members */}
      {activeTab === 'members' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Active Organization Members</h2>
            </div>
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              {filteredMembers.length} members
            </span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={4} />
            </div>
          ) : filteredMembers.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No organization members found matching your search.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-3">Member</th>
                    <th className="px-5 py-3">Organization Role</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Joined Date</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                  {filteredMembers.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold flex items-center justify-center text-xs border border-slate-300 dark:border-slate-600">
                            {m.full_name?.charAt(0) || m.email?.charAt(0).toUpperCase() || 'U'}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 dark:text-white">{m.full_name || 'Active Member'}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{m.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        {canManageMembers && m.role !== 'OWNER' ? (
                          <select
                            value={m.role}
                            disabled={updatingMemberId === m.id}
                            onChange={(e) => handleRoleChange(m.id, e.target.value as TenantRole)}
                            className="px-2 py-1 text-xs font-semibold rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer disabled:opacity-50"
                          >
                            {(activeOrg?.role === 'OWNER' || activeOrg?.role === 'ADMIN') && (
                              <option value="ADMIN">ADMIN</option>
                            )}
                            <option value="FINOPS_MANAGER">FINOPS_MANAGER</option>
                            <option value="ANALYST">ANALYST</option>
                            <option value="VIEWER">VIEWER</option>
                          </select>
                        ) : (
                          <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold uppercase tracking-wider border ${
                            m.role === 'OWNER'
                              ? 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700 font-bold'
                              : m.role === 'ADMIN'
                              ? 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700 font-semibold'
                              : 'bg-slate-50 text-slate-600 dark:bg-slate-800/60 dark:text-slate-400 border-slate-200 dark:border-slate-800'
                          }`}>
                            {m.role}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold">
                          <CheckCircle2 className="w-4 h-4" /> {m.status || 'ACTIVE'}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-500 dark:text-slate-400">
                        {m.created_at || m.joined_at ? new Date(m.created_at || m.joined_at || '').toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-5 py-3 text-right">
                        {canManageMembers && m.role !== 'OWNER' && (
                          <button
                            onClick={() => setMemberToDelete(m)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/30 cursor-pointer"
                            title="Remove Member"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Pending Invitations */}
      {activeTab === 'invitations' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">Pending & Sent Invitations</h2>
            </div>
            <button
              onClick={fetchAllData}
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-white rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
              title="Refresh Invitations"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={3} />
            </div>
          ) : filteredInvitations.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No invitations found. Click &quot;Invite User&quot; above to invite colleagues to this organization.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-3">Invited Email</th>
                    <th className="px-5 py-3">Invited Role</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Expires At</th>
                    <th className="px-5 py-3 text-right">Invite Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                  {filteredInvitations.map((inv) => {
                    const fullInviteLink = `${window.location.origin}${inv.invitation_link}`;
                    const isCopied = copiedToken === inv.id;
                    const isPending = inv.status === 'PENDING';

                    return (
                      <tr key={inv.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <Mail className="w-4 h-4 text-slate-400" />
                            <span className="font-mono font-medium text-slate-900 dark:text-white">{inv.email}</span>
                          </div>
                        </td>
                        <td className="px-5 py-3">
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                            {inv.role}
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <div className="flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 font-bold ${
                              inv.status === 'ACCEPTED'
                                ? 'text-emerald-600 dark:text-emerald-400'
                                : inv.status === 'PENDING'
                                ? 'text-amber-600 dark:text-amber-400'
                                : 'text-slate-400'
                            }`}>
                              {inv.status === 'ACCEPTED' ? (
                                <CheckCircle2 className="w-4 h-4" />
                              ) : (
                                <Clock className="w-4 h-4" />
                              )}
                              {inv.status}
                            </span>
                            {inv.status === 'ACCEPTED' && (
                              <span className="text-[10px] font-medium text-emerald-700 bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-300 px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-800">
                                Auto-removes in 2 days
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-5 py-3 font-mono text-slate-500 dark:text-slate-400">
                          {inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : '7 Days'}
                        </td>
                        <td className="px-5 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {isPending && (
                              <button
                                onClick={() => copyToClipboard(fullInviteLink, inv.id)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/50 border border-blue-200 dark:border-blue-800 rounded-lg transition-colors cursor-pointer"
                                title="Copy Invitation Link"
                              >
                                {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                                <span>{isCopied ? 'Copied!' : 'Copy Link'}</span>
                              </button>
                            )}
                            {canManageMembers && isPending && (
                              <button
                                onClick={() => setInviteToRevoke(inv)}
                                className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/30 cursor-pointer"
                                title="Revoke Invitation"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: All Platform Users */}
      {activeTab === 'all' && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Platform User Directory</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Global directory of registered accounts across the platform.
              </p>
            </div>
            <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2.5 py-1 rounded-full font-medium">
              {filteredUsers.length} Users
            </span>
          </div>

          {loading ? (
            <div className="p-6">
              <LoadingSkeleton rows={4} />
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              No registered platform users found matching your search.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-xs uppercase font-medium text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="px-5 py-3">User</th>
                    <th className="px-5 py-3">System Role</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Registered</th>
                    <th className="px-5 py-3">Last Active</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-xs">
                  {filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold flex items-center justify-center text-xs border border-slate-300 dark:border-slate-600">
                            {u.full_name?.charAt(0) || u.email?.charAt(0).toUpperCase() || 'U'}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 dark:text-white">{u.full_name || 'Platform User'}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{u.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <span className="px-2.5 py-0.5 rounded-md text-[11px] font-bold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700 uppercase">
                          {u.role}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {u.is_active ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold">
                            <CheckCircle2 className="w-4 h-4" /> Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-rose-500 font-bold">
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 font-mono text-slate-500 dark:text-slate-400">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3 text-slate-500 dark:text-slate-400">
                        {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never logged in'}
                      </td>
                      <td className="px-5 py-3 text-right">
                        {canManageMembers && !u.email.endsWith('@cloudcost.local') && (
                          <button
                            onClick={() => setUserToDelete(u)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/30 cursor-pointer"
                            title="Delete User from Platform"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Invite User Modal */}
      {isInviteOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl relative space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-blue-600 dark:text-cyan-400" />
                Invite Member to Organization
              </h3>
              <button
                onClick={() => setIsInviteOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {inviteError && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-500/10 border border-rose-200 dark:border-rose-500/30 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                <span>{inviteError}</span>
              </div>
            )}
            {inviteSuccess && (
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                <span>{inviteSuccess}</span>
              </div>
            )}

            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Colleague Email Address <span className="text-rose-500">*</span>
                </label>
                <div className="relative rounded-xl shadow-xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="colleague@company.com"
                    className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Assigned Organization Role
                </label>
                <div className="relative rounded-xl shadow-xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Shield className="w-4 h-4" />
                  </div>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ADMIN">ADMIN (Full Admin Access)</option>
                    <option value="FINOPS_MANAGER">FINOPS_MANAGER (Manage Costs & Alerts)</option>
                    <option value="ANALYST">ANALYST (Standard FinOps Access)</option>
                    <option value="VIEWER">VIEWER (Read-Only Access)</option>
                  </select>
                </div>
              </div>

              {inviteLink && (
                <div className="p-3 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl space-y-1.5">
                  <span className="text-[11px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                    Invitation Security Link:
                  </span>
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      readOnly
                      value={inviteLink}
                      className="w-full p-1.5 text-[11px] font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-800 dark:text-slate-200"
                    />
                    <button
                      type="button"
                      onClick={() => copyToClipboard(inviteLink, 'modal')}
                      className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors shrink-0 cursor-pointer"
                    >
                      {copiedToken === 'modal' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setIsInviteOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? 'Generating Invite...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Remove Member Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(memberToDelete)}
        onClose={() => setMemberToDelete(null)}
        onConfirm={confirmRemoveMember}
        title="Remove Organization Member"
        message={`Are you sure you want to remove '${memberToDelete?.email || memberToDelete?.full_name || 'this member'}' from the organization?`}
        confirmText="Remove Member"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeletingMember}
      />

      {/* Revoke Invite Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(inviteToRevoke)}
        onClose={() => setInviteToRevoke(null)}
        onConfirm={confirmRevokeInvite}
        title="Revoke Invitation"
        message={`Are you sure you want to revoke the pending invitation for '${inviteToRevoke?.email}'?`}
        confirmText="Revoke Invite"
        cancelText="Cancel"
        variant="warning"
        isLoading={isRevokingInvite}
      />

      {/* Delete User Confirmation Modal */}
      <ConfirmModal
        isOpen={Boolean(userToDelete)}
        onClose={() => setUserToDelete(null)}
        onConfirm={confirmDeleteUser}
        title="Delete Platform User"
        message={`Are you sure you want to permanently delete user '${userToDelete?.email}' from the platform directory?`}
        confirmText="Delete User"
        cancelText="Cancel"
        variant="danger"
        isLoading={isDeletingUser}
      />
    </div>
  );
};

export default AdminUsers;
