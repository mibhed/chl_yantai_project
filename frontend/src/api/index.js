import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  getRegions() {
    return api.get('/regions')
  },
  
  getModels() {
    return api.get('/models')
  },
  
  uploadSamples(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/samples', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  uploadTiff(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/tiff', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  validateSatellite(formData) {
    return api.post('/satellite/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  convertSatellite(formData) {
    return api.post('/satellite/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  downloadConverted(filename) {
    return api.get(`/satellite/download/${filename}`, {
      responseType: 'blob'
    })
  },
  
  trainModel(modelType, cvFolds = 5) {
    return api.post('/training', { model_type: modelType, cv_folds: cvFolds })
  },

  startTraining(modelType, cvFolds = 5) {
    return api.post('/training/start', { model_type: modelType, cv_folds: cvFolds })
  },

  getTrainingResults() {
    return api.get('/training/results')
  },
  
  spatialAnalysis(region, year, month, model) {
    return api.post('/analysis/spatial', { region, year, month, model })
  },
  
  monthlyAnalysis(region, year, model) {
    return api.post('/analysis/monthly', { region, year, model })
  },
  
  multiRegionAnalysis(year, model) {
    return api.post('/analysis/multi-region', { year, model })
  },
  
  multiYearAnalysis(region, startYear, endYear, model) {
    return api.post('/analysis/multi-year', { region, start_year: startYear, end_year: endYear, model })
  },
  
  listFiles(fileType) {
    return api.get('/files/list', { params: { file_type: fileType } })
  },

  healthCheck() {
    return api.get('/health')
  },

  // MODIS L2 相关
  readModisL2(formData) {
    return api.post('/modis/read', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },

  chlaRetrieve(formData) {
    return api.post('/modis/retrieve', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000
    })
  },

  // 使用示例数据执行演示反演
  demoChlaRetrieve(modelType = 'RF', qaMax = 1) {
    return api.post(`/modis/retrieve/demo?model_type=${modelType}&qa_max=${qaMax}`, null, {
      timeout: 300000
    })
  },

  // 使用上传的GeoTIFF执行反演
  retrieveTiffChla(formData) {
    return api.post('/modis/retrieve/tiff', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000
    })
  },

  downloadModisOutput(filename) {
    return api.get(`/modis/download/${filename}`, {
      responseType: 'blob'
    })
  },

  getModisRegions() {
    return api.get('/modis/regions')
  }
}