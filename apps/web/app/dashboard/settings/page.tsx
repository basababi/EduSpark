"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ElementType } from "react";
import { useRouter } from "next/navigation";
import { Bell, LogOut, Save, Settings, Shield, User } from "lucide-react";
import type {
  UserPreferencesPatchRequest,
  UserPreferencesResponse,
  UserProfilePatchRequest,
  UserProfileResponse,
} from "@/lib/api-types";
import {
  getPreferences,
  getProfile,
  logout,
  updatePreferences,
  updateProfile,
} from "@/lib/api-client";
import { handlePageApiError, requireAuthOrRedirect } from "@/lib/page-auth";
import { ApiErrorPanel } from "@/components/ui/ApiErrorPanel";
import { Skeleton } from "@/components/ui/Skeleton";
import { Toast, type ToastState } from "@/components/ui/Toast";

type TabKey = "profile" | "preferences" | "security";

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-2xl border border-neutral-200 bg-white shadow-sm ${className}`}>{children}</div>;
}

function TabButton({
  active,
  label,
  onClick,
  icon: Icon,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
  icon: ElementType;
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${
        active ? "bg-neutral-900 text-white" : "bg-white text-neutral-700 border border-neutral-200"
      }`}
    >
      <Icon size={14} />
      {label}
    </button>
  );
}

function Toggle({ checked, onToggle }: { checked: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      className={`relative h-6 w-11 rounded-full transition-colors ${checked ? "bg-neutral-900" : "bg-neutral-200"}`}
      role="switch"
      aria-checked={checked}
    >
      <span className={`absolute top-1 h-4 w-4 rounded-full bg-white transition-all ${checked ? "left-6" : "left-1"}`} />
    </button>
  );
}

function normalizeInterests(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string");
  }
  if (value && typeof value === "object") {
    return Object.keys(value as Record<string, unknown>);
  }
  return [];
}

export default function SettingsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<TabKey>("profile");
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [preferences, setPreferences] = useState<UserPreferencesResponse | null>(null);
  const [profileDraft, setProfileDraft] = useState<UserProfilePatchRequest>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  const load = useCallback(async () => {
    if (!requireAuthOrRedirect(router)) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const [profileData, preferenceData] = await Promise.all([getProfile(), getPreferences()]);
      setProfile(profileData);
      setPreferences(preferenceData);
      setProfileDraft({
        name: profileData.name ?? "",
        track: profileData.track ?? "",
        locale: profileData.locale ?? "",
        timezone: profileData.timezone ?? "",
        avatar_url: profileData.avatar_url ?? "",
        interests: normalizeInterests(profileData.interests),
      });
    } catch (err) {
      const message = handlePageApiError(err, router);
      setError(message);
      setToast({ variant: "error", message });
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    void load();
  }, [load]);

  const metrics = useMemo(() => {
    if (!preferences) {
      return { enabled: 0 };
    }
    const enabled = Object.values(preferences).filter(Boolean).length;
    return { enabled };
  }, [preferences]);

  const saveProfile = useCallback(async () => {
    if (!profile) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload: UserProfilePatchRequest = {
        name: profileDraft.name,
        track: profileDraft.track,
        locale: profileDraft.locale,
        timezone: profileDraft.timezone,
        avatar_url: profileDraft.avatar_url,
        interests: profileDraft.interests,
      };
      const updated = await updateProfile(payload);
      setProfile(updated);
      setProfileDraft({
        name: updated.name ?? "",
        track: updated.track ?? "",
        locale: updated.locale ?? "",
        timezone: updated.timezone ?? "",
        avatar_url: updated.avatar_url ?? "",
        interests: normalizeInterests(updated.interests),
      });
      setSuccess("Профайл амжилттай хадгалагдлаа.");
      setToast({ variant: "success", message: "Профайл шинэчлэгдлээ." });
    } catch (err) {
      const message = handlePageApiError(err, router);
      setError(message);
      setToast({ variant: "error", message });
    } finally {
      setSaving(false);
    }
  }, [profile, profileDraft, router]);

  const togglePreference = useCallback(async (key: keyof UserPreferencesResponse) => {
    if (!preferences) {
      return;
    }

    const nextValue = !preferences[key];
    const optimistic = { ...preferences, [key]: nextValue };
    setPreferences(optimistic);
    setSuccess(null);
    setError(null);

    try {
      const payload: UserPreferencesPatchRequest = { [key]: nextValue };
      const updated = await updatePreferences(payload);
      setPreferences(updated);
      setSuccess("Тохиргоо шинэчлэгдлээ.");
      setToast({ variant: "success", message: "Тохиргоо хадгалагдлаа." });
    } catch (err) {
      setPreferences(preferences);
      const message = handlePageApiError(err, router);
      setError(message);
      setToast({ variant: "error", message });
    }
  }, [preferences, router]);

  const signOut = useCallback(async () => {
    await logout();
    router.replace("/login");
  }, [router]);

  return (
    <div className="min-h-screen bg-muted px-4 py-6">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <div className="mx-auto max-w-5xl space-y-4">
        <Card className="p-5 flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Тохиргоо</h1>
            <p className="mt-1 text-sm text-neutral-600">Профайл, preference болон session удирдлага</p>
          </div>
          <button
            onClick={() => void load()}
            className="rounded-lg border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50"
          >
            Шинэчлэх
          </button>
        </Card>

        {error && <ApiErrorPanel message={error} onRetry={() => void load()} />}

        {success && (
          <Card className="p-4 border-emerald-200 bg-emerald-50">
            <p className="text-sm text-emerald-700">{success}</p>
          </Card>
        )}

        <Card className="p-4">
          <div className="flex flex-wrap gap-2">
            <TabButton active={tab === "profile"} label="Профайл" icon={User} onClick={() => setTab("profile")} />
            <TabButton active={tab === "preferences"} label="Тохиргоо" icon={Bell} onClick={() => setTab("preferences")} />
            <TabButton active={tab === "security"} label="Аюулгүй байдал" icon={Shield} onClick={() => setTab("security")} />
          </div>
        </Card>

        {loading && (
          <Card className="p-5">
            <Skeleton className="h-5 w-44" />
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 mt-4">
              {[0, 1, 2, 3].map((item) => (
                <div key={item}>
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-10 w-full mt-2" />
                </div>
              ))}
            </div>
          </Card>
        )}

        {!loading && profile && preferences && tab === "profile" && (
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-neutral-900">Профайл мэдээлэл</h2>
              <button
                onClick={() => void saveProfile()}
                disabled={saving}
                className="rounded-lg bg-neutral-900 px-3 py-2 text-sm font-semibold text-white hover:bg-neutral-800 disabled:opacity-60 inline-flex items-center gap-1.5"
              >
                <Save size={14} />
                {saving ? "Хадгалж байна..." : "Хадгалах"}
              </button>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs font-medium text-neutral-500">Нэр</label>
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
                  value={profileDraft.name ?? ""}
                  onChange={(e) => setProfileDraft((prev) => ({ ...prev, name: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-500">Имэйл</label>
                <input className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm bg-neutral-50" value={profile.email} disabled />
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-500">Track</label>
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
                  value={profileDraft.track ?? ""}
                  onChange={(e) => setProfileDraft((prev) => ({ ...prev, track: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-500">Role</label>
                <input className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm bg-neutral-50" value={profile.role ?? "user"} disabled />
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-500">Locale</label>
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
                  value={profileDraft.locale ?? ""}
                  onChange={(e) => setProfileDraft((prev) => ({ ...prev, locale: e.target.value }))}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-neutral-500">Timezone</label>
                <input
                  className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
                  value={profileDraft.timezone ?? ""}
                  onChange={(e) => setProfileDraft((prev) => ({ ...prev, timezone: e.target.value }))}
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-neutral-500">Сонирхол (таслалаар)</label>
              <input
                className="mt-1 w-full rounded-lg border border-neutral-200 px-3 py-2 text-sm"
                value={(profileDraft.interests ?? []).join(", ")}
                onChange={(e) => {
                  const interests = e.target.value
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean);
                  setProfileDraft((prev) => ({ ...prev, interests }));
                }}
              />
            </div>
          </Card>
        )}

        {!loading && preferences && tab === "preferences" && (
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-neutral-900">Preference тохиргоо</h2>
              <span className="rounded-full border border-neutral-200 bg-neutral-50 px-2.5 py-1 text-xs text-neutral-600">
                Идэвхтэй: {metrics.enabled}/5
              </span>
            </div>

            {(
              [
                ["email_notifications", "Имэйл мэдэгдэл"],
                ["weekly_report", "7 хоногийн тайлан"],
                ["daily_reminder", "Өдөр тутмын сануулга"],
                ["dark_mode", "Dark mode"],
                ["compact_view", "Compact view"],
              ] as Array<[keyof UserPreferencesResponse, string]>
            ).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between rounded-lg border border-neutral-200 px-3 py-3">
                <div>
                  <p className="text-sm font-medium text-neutral-900">{label}</p>
                  <p className="text-xs text-neutral-500">{preferences[key] ? "Идэвхтэй" : "Идэвхгүй"}</p>
                </div>
                <Toggle checked={preferences[key]} onToggle={() => void togglePreference(key)} />
              </div>
            ))}
          </Card>
        )}

        {!loading && tab === "security" && (
          <Card className="p-5 space-y-4">
            <div className="flex items-center gap-2">
              <Settings size={16} />
              <h2 className="text-lg font-semibold text-neutral-900">Session ба аюулгүй байдал</h2>
            </div>
            <p className="text-sm text-neutral-600">Нэвтрэлтийн session-ийг дуусгахын тулд logout ашиглана.</p>
            <button
              onClick={() => void signOut()}
              className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 inline-flex items-center gap-1.5"
            >
              <LogOut size={14} />
              Гарах
            </button>
          </Card>
        )}
      </div>
    </div>
  );
}
