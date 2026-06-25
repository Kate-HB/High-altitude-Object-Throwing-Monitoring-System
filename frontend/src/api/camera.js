import request from './request'

export function startCamera() {
  return request.post('/camera/start')
}

export function fetchCameraStatus() {
  return request.get('/camera/status')
}

export function stopCamera() {
  return request.post('/camera/stop')
}
