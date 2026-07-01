import request from './request'

/** POST /api/videos/upload — multipart form upload */
export function uploadVideo(formData, onProgress) {
  return request.post('/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
      ? (e) => {
          if (e.total) onProgress(Math.round((e.loaded / e.total) * 100))
        }
      : undefined,
  })
}

/** POST /api/tasks/{taskId}/analyze — submit ROI, start analysis */
export function analyzeTask(taskId, roi) {
  return request.post(`/tasks/${taskId}/analyze`, roi)
}

/** GET /api/tasks/{taskId} — query progress + events */
export function fetchTask(taskId) {
  return request.get(`/tasks/${taskId}`)
}
