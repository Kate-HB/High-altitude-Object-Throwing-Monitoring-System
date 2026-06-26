import request from './request'

export function fetchSystemStatus() {
  return request.get('/system/status')
}

export function fetchStatisticsOverview() {
  return request.get('/statistics/overview')
}
