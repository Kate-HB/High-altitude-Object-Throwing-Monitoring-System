import request from './request'

export function fetchFile(path) {
  return request.get('/files', { params: { path }, responseType: 'blob' })
}
