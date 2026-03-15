<template>
  <div class="model-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🤖 模型选择与训练</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-form-item label="选择模型">
          <el-select v-model="form.modelType" placeholder="请选择模型类型">
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="`${model.name} (${model.id})`"
              :value="model.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="交叉验证折数">
          <el-input-number v-model="form.cvFolds" :min="3" :max="10" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="trainModel" :loading="training">
            开始训练
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="trainingResult" class="result-card">
      <template #header>
        <span>训练结果</span>
      </template>
      <el-result
        :icon="trainingResult.success ? 'success' : 'error'"
        :title="trainingResult.message"
      >
        <template #extra>
          <div v-if="trainingResult.success && trainingResult.data">
            <p>模型类型: {{ trainingResult.data.model_type }}</p>
            <p>特征列: {{ trainingResult.data.feature_columns?.join(', ') }}</p>
          </div>
        </template>
      </el-result>
    </el-card>

    <el-card v-if="results.length > 0" class="results-card">
      <template #header>
        <span>模型评估结果</span>
      </template>
      <el-table :data="results" stripe>
        <el-table-column prop="model" label="模型" />
        <el-table-column prop="R2" label="R²" />
        <el-table-column prop="RMSE" label="RMSE" />
        <el-table-column prop="Bias" label="Bias" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const form = ref({
  modelType: 'RF',
  cvFolds: 5
})
const training = ref(false)
const trainingResult = ref(null)
const results = ref([])
const models = ref([])

const trainModel = async () => {
  training.value = true
  trainingResult.value = null
  
  try {
    const res = await api.trainModel(form.value.modelType, form.value.cvFolds)
    trainingResult.value = res
    if (res.success) {
      ElMessage.success('模型训练完成')
      await loadResults()
    } else {
      ElMessage.error(res.message || '训练失败')
    }
  } catch (e) {
    ElMessage.error('训练失败: ' + e.message)
  } finally {
    training.value = false
  }
}

const loadResults = async () => {
  try {
    const res = await api.getTrainingResults()
    if (res.success && res.data) {
      results.value = res.data
    }
  } catch (e) {
    console.error('Failed to load results:', e)
  }
}

onMounted(async () => {
  await store.fetchModels()
  models.value = store.models
  await loadResults()
})
</script>

<style scoped>
.model-view {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.result-card {
  margin-top: 20px;
}

.results-card {
  margin-top: 20px;
}
</style>