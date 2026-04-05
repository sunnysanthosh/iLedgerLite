import { userClient } from "./client"
import type { OrgMemberInvite, OrgMemberPatch, OrgMemberResponse, OrgResponse } from "@/types/api"

export async function getOrg(orgId: string): Promise<OrgResponse> {
  const res = await userClient.get<OrgResponse>(`/organisations/${orgId}`)
  return res.data
}

export async function listOrgMembers(orgId: string): Promise<OrgMemberResponse[]> {
  const res = await userClient.get<OrgMemberResponse[]>(`/organisations/${orgId}/members`)
  return res.data
}

export async function inviteMember(orgId: string, data: OrgMemberInvite): Promise<OrgMemberResponse> {
  const res = await userClient.post<OrgMemberResponse>(`/organisations/${orgId}/members`, data)
  return res.data
}

export async function updateMemberRole(orgId: string, userId: string, data: OrgMemberPatch): Promise<OrgMemberResponse> {
  const res = await userClient.patch<OrgMemberResponse>(`/organisations/${orgId}/members/${userId}`, data)
  return res.data
}

export async function removeMember(orgId: string, userId: string): Promise<void> {
  await userClient.delete(`/organisations/${orgId}/members/${userId}`)
}
