"use client"

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { updateProfile, updateSettings, deactivateAccount } from "@/lib/api/users"
import { useAuthStore } from "@/lib/store/auth-store"
import type { Language } from "@/types/api"

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "en", label: "English" },
  { value: "hi", label: "हिन्दी (Hindi)" },
  { value: "ta", label: "தமிழ் (Tamil)" },
  { value: "te", label: "తెలుగు (Telugu)" },
]

const CURRENCIES = ["INR", "USD", "EUR", "GBP", "AED", "SGD"]

export default function SettingsPage() {
  const qc = useQueryClient()
  const router = useRouter()
  const { user, setUser, logout } = useAuthStore()

  const [name, setName]   = useState(user?.full_name ?? "")
  const [phone, setPhone] = useState(user?.phone ?? "")
  const [saved, setSaved] = useState(false)

  const profileMutation = useMutation({
    mutationFn: () => updateProfile({ full_name: name, phone: phone || undefined }),
    onSuccess: (updated) => {
      setUser({ ...updated, settings: user!.settings })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  const settingsMutation = useMutation({
    mutationFn: (data: Parameters<typeof updateSettings>[0]) => updateSettings(data),
    onSuccess: (updated) => {
      setUser(updated)
      qc.invalidateQueries({ queryKey: ["profile"] })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: deactivateAccount,
    onSuccess: () => {
      logout()
      router.push("/login")
    },
  })

  function handleSettingToggle(key: "notifications_enabled", value: boolean) {
    settingsMutation.mutate({ [key]: value })
  }

  function handleLanguageChange(lang: Language) {
    settingsMutation.mutate({ language: lang })
  }

  function handleCurrencyChange(currency: string) {
    settingsMutation.mutate({ currency })
  }

  return (
    <div className="space-y-6 max-w-xl">
      <h2 className="text-xl font-semibold text-gray-900">Settings</h2>

      {/* Profile */}
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <p className="text-sm font-semibold text-gray-700">Profile</p>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Full name</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Email</label>
          <p className="text-sm text-gray-400 px-3 py-2 border rounded-lg bg-gray-50">
            {user?.email}
          </p>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Phone</label>
          <input
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="e.g. +91 98765 43210"
          />
        </div>
        <button
          onClick={() => profileMutation.mutate()}
          disabled={profileMutation.isPending}
          className="bg-brand-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-brand-700 disabled:opacity-50"
        >
          {profileMutation.isPending ? "Saving…" : saved ? "Saved!" : "Save Profile"}
        </button>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-xl border p-6 space-y-4">
        <p className="text-sm font-semibold text-gray-700">Preferences</p>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Currency</label>
          <select
            value={user?.settings?.currency ?? "INR"}
            onChange={(e) => handleCurrencyChange(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Language</label>
          <select
            value={user?.settings?.language ?? "en"}
            onChange={(e) => handleLanguageChange(e.target.value as Language)}
            className="w-full border rounded-lg px-3 py-2 text-sm"
          >
            {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700">Notifications</p>
            <p className="text-xs text-gray-400">Receive payment reminders</p>
          </div>
          <button
            onClick={() => handleSettingToggle("notifications_enabled", !user?.settings?.notifications_enabled)}
            className={`w-11 h-6 rounded-full transition-colors ${
              user?.settings?.notifications_enabled ? "bg-brand-600" : "bg-gray-200"
            }`}
          >
            <span
              className={`block w-4 h-4 rounded-full bg-white shadow mx-1 transition-transform ${
                user?.settings?.notifications_enabled ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </div>

      {/* Danger zone */}
      <div className="bg-white rounded-xl border border-red-200 p-6 space-y-3">
        <p className="text-sm font-semibold text-red-700">Danger Zone</p>
        <p className="text-xs text-gray-500">
          Deactivating your account will hide all your data. This action can be reversed by contacting support.
        </p>
        <div className="flex gap-3">
          <button
            onClick={() => { if (confirm("Deactivate account?")) deactivateMutation.mutate() }}
            disabled={deactivateMutation.isPending}
            className="border border-red-500 text-red-600 text-sm px-4 py-2 rounded-lg hover:bg-red-50 disabled:opacity-50"
          >
            Deactivate account
          </button>
          <button
            onClick={() => { logout(); router.push("/login") }}
            className="border text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50"
          >
            Log out
          </button>
        </div>
      </div>
    </div>
  )
}
