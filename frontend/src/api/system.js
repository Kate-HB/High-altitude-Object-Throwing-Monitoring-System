import request from './request'

export function fetchSystemStatus() {
  return request.get('/system/status')
}
