<template>
  <div class="results-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📊 分析结果展示</span>
          <el-button size="small" @click="refresh" :loading="loading">
            刷新
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="模型对比" name="models">
          <el-table :data="modelResults" stripe v-if="modelResults.length > 0" :loading="loading">
            <el-table-column prop="model" label="模型" />
            <el-table-column prop="R2" label="R²">
              <template #default="scope">
                {{ scope.row.R2?.toFixed(4) || 'N/A' }}
              </template>
            </el-table-column>
            <el-table-column prop="RMSE" label="RMSE">
              <template #default="scope">
                {{ scope.row.RMSE?.toFixed(4) || 'N/A' }}
              </template>
            </el-table-column>
            <el-table-column prop="Bias" label="偏差">
              <template #default="scope">
                {{ scope.row.Bias?.toFixed(4) || 'N/A' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else-if="!loading" description="暂无模型训练结果，请先在模型训练页面训练模型" />
        </el-tab-pane>

        <el-tab-pane label="输出文件" name="files">
          <el-table :data="files" stripe v-if="files.length > 0" :loading="loading">
            <el-table-column prop="name" label="文件名" />
            <el-table-column prop="path" label="路径" show-overflow-tooltip />
            <el-table-column label="大小" width="120">
              <template #default="scope">
                {{ formatSize(scope.row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" type="primary" @click="downloadFile(scope.row)">
                  下载
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else-if="!loading" description="暂无输出文件" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const activeTab = ref('models')
const modelResults = ref([])
const files = ref([])
const loading = ref(false)

const formatSize = (bytes) => {
  if (!bytes) return 'N/A'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const loadResults = async () => {
  loading.value = true
  try {
    console.log('[Results] Loading training results...')
    const res = await api.getTrainingResults()
    console.log('[Results] Training results response:', res)

    if (res && res.success && Array.isArray(res.data)) {
      modelResults.value = res.data
    } else {
      modelResults.value = []
    }
  } catch (e) {
    console.error('[Results] Failed to load results:', e)
    ElMessage.error('加载训练结果失败: ' + (e.message || '未知错误'))
    modelResults.value = []
  } finally {
    loading.value = false
  }
}

const loadFiles = async () => {
  loading.value = true
  try {
    console.log('[Results] Loading output files...')
    const res = await api.listFiles()
    console.log('[Results] Files response:', res)

    if (res && res.success && Array.isArray(res.data)) {
      files.value = res.data
    } else {
      files.value = []
    }
  } catch (e) {
    console.error('[Results] Failed to load files:', e)
    ElMessage.error('加载文件列表失败: ' + (e.message || '未知错误'))
    files.value = []
  } finally {
    loading.value = false
  }
}

const downloadFile = (file) => {
  if (file.path) {
    const downloadUrl = `/api/files/${file.path}`
    window.open(downloadUrl, '_blank')
    ElMessage.success('开始下载: ' + file.name)
  }
}

const refresh = async () => {
  if (activeTab.value === 'models') {
    await loadResults()
  } else {
    await loadFiles()
  }
}

const onTabChange = (tabName) => {
  if (tabName === 'models' && modelResults.value.length === 0) {
    loadResults()
  } else if (tabName === 'files' && files.value.length === 0) {
    loadFiles()
  }
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.results-view {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}
</style>