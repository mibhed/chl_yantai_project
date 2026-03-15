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
    tiffUploaded: false
  }),

  actions: {
    async fetchRegions() {
      try {
        const res = await api.getRegions()
        if (res.success) {
          this.regions = res.data
        }
      } catch (e) {
        console.error('Failed to fetch regions:', e)
      }
    },

    async fetchModels() {
      try {
        const res = await api.getModels()
        if (res.success) {
          this.models = res.data
        }
      } catch (e) {
        console.error('Failed to fetch models:', e)
      }
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
    }
  }
})