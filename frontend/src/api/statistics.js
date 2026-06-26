import request from './request'

export function fetchOverview() {
  return request.get('/statistics/overview')
}
