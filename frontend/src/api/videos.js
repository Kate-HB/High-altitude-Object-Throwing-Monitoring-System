import request from './request'

export function uploadVideo(formData, onProgress) {
  return request.post('/videos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
}

export function analyzeTask(taskId, roi) {
  return request.post(`/tasks/${taskId}/analyze`, roi)
}

export function fetchTask(taskId) {
  return request.get(`/tasks/${taskId}`)
}
