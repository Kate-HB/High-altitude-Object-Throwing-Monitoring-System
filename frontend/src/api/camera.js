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

export function startCameraAI(roi, settings) {
  return request.post('/camera/ai/start', {
    roi_x: roi.x,
    roi_y: roi.y,
    roi_width: roi.width,
    roi_height: roi.height,
    ...settings,
  })
}

export function stopCameraAI() {
  return request.post('/camera/ai/stop')
}

export function fetchCameraAIStatus() {
  return request.get('/camera/ai/status')
}
