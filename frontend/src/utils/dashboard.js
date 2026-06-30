export function formatHealthStatus(health) {
  return health?.status === 'running' || health?.status === 'ok'
}

export function normalizeOverview(overview) {
  return {
    today_event_count: overview?.today_event_count ?? '--',
    total_event_count: overview?.total_event_count ?? '--',
    recent_events: overview?.recent_events ?? [],
    daily_trend: overview?.daily_trend ?? [],
    confidence_distribution: overview?.confidence_distribution || {
      'low_0.35_0.5': 0,
      'mid_0.5_0.7': 0,
      'high_0.7_1.0': 0,
    },
    status_distribution: overview?.status_distribution || {
      unconfirmed: 0,
      confirmed: 0,
      false_alarm: 0,
    },
  }
}

export function normalizeTaskProgress(task) {
  if (!task) return 0
  const value = Number.isFinite(task.progress)
    ? task.progress
    : task.total_frames > 0
      ? (task.processed_frames / task.total_frames) * 100
      : 0
  return Math.max(0, Math.min(100, Math.round(value)))
}
