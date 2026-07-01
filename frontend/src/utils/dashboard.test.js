import test from 'node:test'
import assert from 'node:assert/strict'
import {
  formatHealthStatus,
  normalizeOverview,
  normalizeTaskProgress,
} from './dashboard.js'

test('formatHealthStatus accepts running health response', () => {
  assert.equal(formatHealthStatus({ status: 'running' }), true)
  assert.equal(formatHealthStatus({ status: 'ok' }), true)
  assert.equal(formatHealthStatus({ status: 'failed' }), false)
})

test('normalizeOverview fills dashboard fallback values', () => {
  assert.deepEqual(normalizeOverview(null), {
    today_event_count: '--',
    total_event_count: '--',
    recent_events: [],
    daily_trend: [],
  })
  assert.equal(normalizeOverview({ today_event_count: 2 }).today_event_count, 2)
})

test('normalizeTaskProgress clamps progress to 0-100', () => {
  assert.equal(normalizeTaskProgress({ progress: 120 }), 100)
  assert.equal(normalizeTaskProgress({ processed_frames: 3, total_frames: 6 }), 50)
  assert.equal(normalizeTaskProgress({ processed_frames: 3, total_frames: 0 }), 0)
})
