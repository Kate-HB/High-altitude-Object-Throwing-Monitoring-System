import request from './request'

export function startCamera(cameraIndex = 0, width = 640, height = 480) {
  return request.post('/camera/start', { camera_index: cameraIndex, width, height })
}

export function fetchCameraStatus() {
  return request.get('/camera/status')
}

export function stopCamera() {
  return request.post('/camera/stop')
}
