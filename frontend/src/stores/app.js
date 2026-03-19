import { defineStore } from 'pinia'
import api from '@/api'

export const useAppStore = defineStore('app', {
  state: () => ({
    regions: [],
    models: [],
    currentRegion: '烟台近岸整体',
    currentYear: new Date().getFullYear(),
    currentMonth: new Date().getMonth() + 1,
    currentModel: 'RF',
    loading: false,
    samplesUploaded: false,
    tiffUploaded: false,
    error: null,
    initialized: false
  }),

  actions: {
    async fetchRegions() {
      this.loading = true
      this.error = null
      try {
        console.log('[Store] Fetching regions from API...')
        const res = await api.getRegions()
        console.log('[Store] Regions API response:', res)

        if (res && res.success && Array.isArray(res.data)) {
          this.regions = res.data
          console.log('[Store] Regions loaded:', this.regions.length)

          if (this.regions.length > 0 && !this.initialized) {
            this.currentRegion = this.regions[0].name
          }
        } else {
          console.warn('[Store] Invalid regions response:', res)
          this.error = '获取区域列表失败'
        }
      } catch (e) {
        console.error('[Store] Failed to fetch regions:', e)
        this.error = '获取区域列表失败: ' + (e.message || '未知错误')
      } finally {
        this.loading = false
      }
    },

    async fetchModels() {
      this.loading = true
      this.error = null
      try {
        console.log('[Store] Fetching models from API...')
        const res = await api.getModels()
        console.log('[Store] Models API response:', res)

        if (res && res.success && Array.isArray(res.data)) {
          this.models = res.data
          console.log('[Store] Models loaded:', this.models.length)

          if (this.models.length > 0 && !this.initialized) {
            this.currentModel = this.models[0].id
            this.initialized = true
          }
        } else {
          console.warn('[Store] Invalid models response:', res)
          this.error = '获取模型列表失败'
        }
      } catch (e) {
        console.error('[Store] Failed to fetch models:', e)
        this.error = '获取模型列表失败: ' + (e.message || '未知错误')
      } finally {
        this.loading = false
      }
    },

    async initialize() {
      console.log('[Store] Initializing store...')
      await Promise.all([
        this.fetchRegions(),
        this.fetchModels()
      ])
      console.log('[Store] Store initialized')
    },

    setRegion(region) {
      this.currentRegion = region
    },

    setYear(year) {
      this.currentYear = year
    },

    setMonth(month) {
      this.currentMonth = month
    },

    setModel(model) {
      this.currentModel = model
    },

    setLoading(loading) {
      this.loading = loading
    },

    setSamplesUploaded(uploaded) {
      this.samplesUploaded = uploaded
    },

    setTiffUploaded(uploaded) {
      this.tiffUploaded = uploaded
    },

    clearError() {
      this.error = null
    }
  }
})