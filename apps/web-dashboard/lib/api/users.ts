import { userClient } from "./client"
import type {
  UserProfileWithSettings,
  UserUpdate,
  SettingsUpdate,
  OnboardingRequest,
} from "@/types/api"

export async function getProfile(): Promise<UserProfileWithSettings> {
  const res = await userClient.get<UserProfileWithSettings>("/users/me")
  return res.data
}

export async function updateProfile(data: UserUpdate): Promise<UserProfileWithSettings> {
  const res = await userClient.put<UserProfileWithSettings>("/users/me", data)
  return res.data
}

export async function updateSettings(data: SettingsUpdate): Promise<UserProfileWithSettings> {
  const res = await userClient.put<UserProfileWithSettings>("/users/me/settings", data)
  return res.data
}

export async function completeOnboarding(data: OnboardingRequest): Promise<void> {
  await userClient.post("/users/me/onboarding", data)
}

export async function deactivateAccount(): Promise<void> {
  await userClient.delete("/users/me")
}
