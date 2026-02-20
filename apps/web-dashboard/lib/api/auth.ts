import { authClient } from "./client"
import type { LoginRequest, RegisterRequest, TokenResponse, UserProfile } from "@/types/api"

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>("/auth/login", data)
  return res.data
}

export async function register(data: RegisterRequest): Promise<UserProfile> {
  const res = await authClient.post<UserProfile>("/auth/register", data)
  return res.data
}

export async function refresh(refreshToken: string): Promise<TokenResponse> {
  const res = await authClient.post<TokenResponse>("/auth/refresh", {
    refresh_token: refreshToken,
  })
  return res.data
}

export async function getMe(): Promise<UserProfile> {
  const res = await authClient.get<UserProfile>("/auth/me")
  return res.data
}
