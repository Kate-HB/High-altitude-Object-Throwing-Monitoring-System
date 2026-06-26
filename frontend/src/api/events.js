import request from './request'

export function fetchEvents(params) {
  return request.get('/events', { params })
}

export function fetchEvent(id) {
  return request.get(`/events/${id}`)
}

export function updateEventStatus(id, status) {
  return request.patch(`/events/${id}/status`, { status })
}
