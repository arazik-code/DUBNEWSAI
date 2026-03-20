"use client"

import { type ReactNode, useMemo, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Building2, Plus, Share2, Users2, Workflow } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useTeamActivity, useTeams } from "@/lib/hooks/useEnterprise"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

export default function TeamsPage() {
  const queryClient = useQueryClient()
  const { data: teams = [] } = useTeams()
  const [selectedId, setSelectedId] = useState<number | undefined>(undefined)
  const [teamForm, setTeamForm] = useState({ name: "Dubai Strategy Cell", description: "Shared command room for investment, research, and strategy." })
  const [memberForm, setMemberForm] = useState({ user_id: 1, role: "member" })
  const [shareForm, setShareForm] = useState({ item_type: "portfolio", item_id: 1, item_name: "Dubai Growth Sleeve", description: "Shared with the strategy cell for review." })

  const selected = useMemo(() => teams.find((item) => item.id === selectedId) || teams[0], [teams, selectedId])
  const { data: activity = [] } = useTeamActivity(selected?.id)

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
          description="Phase 6 gives DUBNEWSAI the collaboration layer it needs for real firms: shared items, team activity, role-based membership, and an operating history that can be audited."
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
              <button onClick={() => createTeam.mutate()} className="action-premium mt-5">
                <Plus className="h-4 w-4" />
                Create team
              </button>
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
                      <Field label="User id">
                        <input type="number" className="input-premium" value={memberForm.user_id} onChange={(event) => setMemberForm((current) => ({ ...current, user_id: Number(event.target.value) }))} />
                      </Field>
                      <Field label="Role">
                        <select className="input-premium" value={memberForm.role} onChange={(event) => setMemberForm((current) => ({ ...current, role: event.target.value }))}>
                          <option value="member">Member</option>
                          <option value="viewer">Viewer</option>
                          <option value="admin">Admin</option>
                        </select>
                      </Field>
                    </div>
                    <button onClick={() => addMember.mutate()} className="action-premium mt-5">
                      <Users2 className="h-4 w-4" />
                      Add member
                    </button>
                  </div>

                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Share item</div>
                    <div className="mt-4 grid gap-4">
                      <Field label="Item type">
                        <select className="input-premium" value={shareForm.item_type} onChange={(event) => setShareForm((current) => ({ ...current, item_type: event.target.value }))}>
                          <option value="portfolio">Portfolio</option>
                          <option value="watchlist">Watchlist</option>
                          <option value="insight">Insight</option>
                          <option value="report">Report</option>
                        </select>
                      </Field>
                      <Field label="Item id">
                        <input type="number" className="input-premium" value={shareForm.item_id} onChange={(event) => setShareForm((current) => ({ ...current, item_id: Number(event.target.value) }))} />
                      </Field>
                      <Field label="Item name">
                        <input className="input-premium" value={shareForm.item_name} onChange={(event) => setShareForm((current) => ({ ...current, item_name: event.target.value }))} />
                      </Field>
                    </div>
                    <button onClick={() => shareItem.mutate()} className="action-premium mt-5">
                      <Share2 className="h-4 w-4" />
                      Share into team
                    </button>
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
