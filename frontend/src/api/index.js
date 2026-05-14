import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const annotationApi = {
  list: () => api.get('/annotation/list'),
  uploadImage: (formData) => api.post('/annotation/upload', formData),
  uploadJson: (formData) => api.post('/annotation/json/upload', formData),
  delete: (name) => api.delete(`/annotation/${name}`)
}

export const trainingApi = {
  list: () => api.get('/training/list'),
  upload: (formData) => api.post('/training/upload', formData),
  delete: (name) => api.delete(`/training/${name}`)
}

export const proofreadingApi = {
  list: () => api.get('/proofreading/list'),
  upload: (formData) => api.post('/proofreading/upload', formData),
  delete: (name) => api.delete(`/proofreading/${name}`)
}

export const networkApi = {
  info: () => api.get('/network/info')
}

export default api
