<template>
  <div class="results-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📊 分析结果展示</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="模型对比" name="models">
          <el-table :data="modelResults" stripe v-if="modelResults.length > 0">
            <el-table-column prop="model" label="模型" />
            <el-table-column prop="R2" label="R²" />
            <el-table-column prop="RMSE" label="RMSE" />
            <el-table-column prop="Bias" label="偏差" />
          </el-table>
          <el-empty v-else description="暂无模型训练结果" />
        </el-tab-pane>

        <el-tab-pane label="输出文件" name="files">
          <el-table :data="files" stripe v-if="files.length > 0">
            <el-table-column prop="name" label="文件名" />
            <el-table-column prop="path" label="路径" />
            <el-table-column label="大小">
              <template #default="scope">
                {{ formatSize(scope.row.size) }}
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button size="small" type="primary">下载</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无输出文件" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const activeTab = ref('models')
const modelResults = ref([])
const files = ref([])

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const loadResults = async () => {
  try {
    const res = await api.getTrainingResults()
    if (res.success && res.data) {
      modelResults.value = res.data
    }
  } catch (e) {
    console.error('Failed to load results:', e)
  }
}

const loadFiles = async () => {
  try {
    const res = await api.listFiles()
    if (res.success && res.data) {
      files.value = res.data
    }
  } catch (e) {
    console.error('Failed to load files:', e)
  }
}

onMounted(() => {
  loadResults()
  loadFiles()
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