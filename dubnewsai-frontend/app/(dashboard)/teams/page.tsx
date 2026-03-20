"use client"

import { type ReactNode, useEffect, useMemo, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Building2, Plus, Share2, Users2, Workflow } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ActionStatus } from "@/components/shared/ActionStatus"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useTeamActivity, useTeamDirectory, useTeams } from "@/lib/hooks/useEnterprise"
import { usePortfolios, useWatchlists } from "@/lib/hooks/usePortfolio"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

export default function TeamsPage() {
  const queryClient = useQueryClient()
  const { data: teams = [] } = useTeams()
  const { data: portfolios = [] } = usePortfolios()
  const { data: watchlists = [] } = useWatchlists()
  const { data: directory = [] } = useTeamDirectory()
  const [selectedId, setSelectedId] = useState<number | undefined>(undefined)
  const [teamForm, setTeamForm] = useState({ name: "Dubai Strategy Cell", description: "Shared command room for investment, research, and strategy." })
  const [memberForm, setMemberForm] = useState({ user_id: 0, role: "member" })
  const [shareForm, setShareForm] = useState({ item_type: "portfolio", item_id: 0, item_name: "", description: "Shared with the strategy cell for review." })

  const selected = useMemo(() => teams.find((item) => item.id === selectedId) || teams[0], [teams, selectedId])
  const shareableItems = useMemo(() => {
    if (shareForm.item_type === "watchlist") {
      return watchlists.map((item) => ({ id: item.id, name: item.name }))
    }
    return portfolios.map((item) => ({ id: item.id, name: item.name }))
  }, [portfolios, shareForm.item_type, watchlists])
  const { data: activity = [] } = useTeamActivity(selected?.id)

  useEffect(() => {
    if (memberForm.user_id === 0 && directory[0]) {
      setMemberForm((current) => ({ ...current, user_id: directory[0].id }))
    }
  }, [directory, memberForm.user_id])

  useEffect(() => {
    if (shareableItems[0] && (shareForm.item_id === 0 || !shareableItems.some((item) => item.id === shareForm.item_id))) {
      setShareForm((current) => ({ ...current, item_id: shareableItems[0].id, item_name: shareableItems[0].name }))
    }
  }, [shareForm.item_id, shareableItems])

  const createTeam = useMutation({
    mutationFn: async () => {
      await apiClient.post("/teams", teamForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams"] })
    }
  })

  const addMember = useMutation({
    mutationFn: async () => {
      if (!selected?.id) return
      await apiClient.post(`/teams/${selected.id}/members`, memberForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams", selected?.id, "activity"] })
    }
  })

  const shareItem = useMutation({
    mutationFn: async () => {
      if (!selected?.id) return
      await apiClient.post(`/teams/${selected.id}/share`, shareForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["teams", selected?.id, "activity"] })
    }
  })

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Team collaboration"
          title="Share portfolios, insights, and decisions inside a live strategy workspace."
          description="A simpler collaboration layer for sharing books, insights, and activity across the team."
          chips={["Shared portfolios", "Team activity", "Role-aware membership", "Operational memory"]}
          stats={[
            { label: "Teams", value: `${teams.length}`, hint: "Active collaboration spaces in this workspace" },
            { label: "Selected team", value: selected?.name || "None", hint: selected?.description || "Choose a team to inspect" },
            { label: "Recent activity", value: `${activity.length}`, hint: "Latest events in the selected space" },
            { label: "Sharing mode", value: "Live", hint: "Portfolios, watchlists, and insights can be shared" }
          ]}
          tone="cyan"
        />

        <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Team registry</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Command rooms and shared workspaces</h2>
            <div className="mt-6 space-y-3">
              {teams.map((team) => (
                <button
                  key={team.id}
                  onClick={() => setSelectedId(team.id)}
                  className={`w-full rounded-[1.5rem] border p-4 text-left transition ${
                    selected?.id === team.id ? "border-cyan-300/30 bg-cyan-300/[0.08]" : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-white">{team.name}</div>
                      <div className="mt-1 text-xs text-white/44">{team.description}</div>
                    </div>
                    <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/58">
                      {team.max_members} seats
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-8 rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Create team</div>
              <div className="mt-4 grid gap-4">
                <Field label="Team name">
                  <input className="input-premium" value={teamForm.name} onChange={(event) => setTeamForm((current) => ({ ...current, name: event.target.value }))} />
                </Field>
                <Field label="Description">
                  <input className="input-premium" value={teamForm.description} onChange={(event) => setTeamForm((current) => ({ ...current, description: event.target.value }))} />
                </Field>
              </div>
              <button onClick={() => createTeam.mutate()} className="action-premium mt-5" disabled={createTeam.isPending}>
                <Plus className="h-4 w-4" />
                {createTeam.isPending ? "Creating..." : "Create team"}
              </button>
              <ActionStatus
                isPending={createTeam.isPending}
                isSuccess={createTeam.isSuccess}
                error={createTeam.error}
                successMessage="Team created."
              />
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Selected team</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">{selected?.name || "Choose a team"}</h2>
            {selected ? (
              <div className="mt-6 space-y-6">
                <div className="grid gap-4 md:grid-cols-3">
                  <MetricTile icon={Users2} label="Seat limit" value={`${selected.max_members}`} />
                  <MetricTile icon={Share2} label="Shared portfolios" value={selected.shared_portfolios ? "Enabled" : "Disabled"} />
                  <MetricTile icon={Workflow} label="Shared insights" value={selected.shared_insights ? "Enabled" : "Disabled"} />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Add member</div>
                    <div className="mt-4 grid gap-4">
                      <Field label="Team member">
                        <select className="input-premium" value={memberForm.user_id} onChange={(event) => setMemberForm((current) => ({ ...current, user_id: Number(event.target.value) }))}>
                          {directory.map((item) => (
                            <option key={item.id} value={item.id}>
                              {(item.full_name || item.email) + " - " + item.role}
                            </option>
                          ))}
                        </select>
                      </Field>
                      <Field label="Role">
                        <select className="input-premium" value={memberForm.role} onChange={(event) => setMemberForm((current) => ({ ...current, role: event.target.value }))}>
                          <option value="member">Member</option>
                          <option value="viewer">Viewer</option>
                          <option value="admin">Admin</option>
                        </select>
                      </Field>
                    </div>
                    <button onClick={() => addMember.mutate()} className="action-premium mt-5" disabled={addMember.isPending || !directory.length}>
                      <Users2 className="h-4 w-4" />
                      {addMember.isPending ? "Adding..." : "Add member"}
                    </button>
                    <ActionStatus
                      isPending={addMember.isPending}
                      isSuccess={addMember.isSuccess}
                      error={addMember.error}
                      successMessage="Member added."
                    />
                  </div>

                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Share item</div>
                    <div className="mt-4 grid gap-4">
                      <Field label="Item type">
                        <select className="input-premium" value={shareForm.item_type} onChange={(event) => setShareForm((current) => ({ ...current, item_type: event.target.value }))}>
                          <option value="portfolio">Portfolio</option>
                          <option value="watchlist">Watchlist</option>
                        </select>
                      </Field>
                      <Field label="Shareable item">
                        <select
                          className="input-premium"
                          value={shareForm.item_id}
                          onChange={(event) => {
                            const item = shareableItems.find((candidate) => candidate.id === Number(event.target.value))
                            setShareForm((current) => ({
                              ...current,
                              item_id: Number(event.target.value),
                              item_name: item?.name || current.item_name
                            }))
                          }}
                        >
                          {shareableItems.map((item) => (
                            <option key={`${shareForm.item_type}-${item.id}`} value={item.id}>
                              {item.name}
                            </option>
                          ))}
                        </select>
                      </Field>
                    </div>
                    <button onClick={() => shareItem.mutate()} className="action-premium mt-5" disabled={shareItem.isPending || !shareableItems.length}>
                      <Share2 className="h-4 w-4" />
                      {shareItem.isPending ? "Sharing..." : "Share into team"}
                    </button>
                    <ActionStatus
                      isPending={shareItem.isPending}
                      isSuccess={shareItem.isSuccess}
                      error={shareItem.error}
                      successMessage="Item shared with team."
                    />
                  </div>
                </div>

                <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
                    <Building2 className="h-3.5 w-3.5 text-cyan-200" />
                    Activity feed
                  </div>
                  <div className="mt-4 space-y-3">
                    {activity.map((item) => (
                      <div key={item.id} className="rounded-[1.2rem] border border-white/10 bg-white/[0.02] p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div className="text-sm font-medium text-white">{titleCase(item.activity_type)}</div>
                          <div className="text-xs text-white/40">{formatDateTime(item.created_at)}</div>
                        </div>
                        <div className="mt-2 text-sm leading-7 text-white/56">{item.description}</div>
                        {item.user ? <div className="mt-2 text-xs text-white/40">{item.user.full_name || item.user.email}</div> : null}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-6 rounded-[1.6rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm text-white/46">
                Create or choose a team to start sharing portfolios, reports, and intelligence.
              </div>
            )}
          </article>
        </section>
      </div>
    </AuthGuard>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      {children}
    </label>
  )
}

function MetricTile({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Building2 }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <div className="mt-3 text-xl font-semibold text-white">{value}</div>
    </div>
  )
}
