<template>
  <div class="model-view">
    <!-- 实时进度条 -->
    <el-card v-if="training" class="progress-card">
      <template #header>
        <span>训练进度</span>
      </template>
      <el-progress
        :percentage="progressPct"
        :status="progressPct >= 100 ? 'success' : undefined"
        :stroke-width="20"
      />
      <p class="progress-stage">{{ progressStage }}</p>
      <p class="progress-msg">{{ progressMsg }}</p>
    </el-card>

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
import { ref, onMounted, computed } from 'vue'
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
const models = computed(() => store.models)

const progressPct = ref(0)
const progressStage = ref('')
const progressMsg = ref('')
let eventSource = null

const trainModel = async () => {
  training.value = true
  trainingResult.value = null
  progressPct.value = 0
  progressStage.value = '准备启动...'
  progressMsg.value = ''

  try {
    // 1. 启动后端训练，获取 stream_id
    const startRes = await api.startTraining(form.value.modelType, form.value.cvFolds)
    const { stream_id } = startRes

    // 2. 用 stream_id 打开 SSE 监听实时进度
    eventSource = new EventSource(`/api/training/stream?stream_id=${stream_id}`)

    eventSource.addEventListener('progress', (e) => {
      try {
        const d = JSON.parse(e.data)
        progressPct.value = d.pct
        progressStage.value = stageLabel(d.stage)
        progressMsg.value = d.msg || ''
      } catch {}
    })

    eventSource.addEventListener('ping', () => {})

    eventSource.onerror = () => {
      // 连接断开时不中断，等待 fetch 完成
    }

    // 3. 等待后端训练真正完成（fetch 原本的训练接口）
    console.log('[Model] Starting training:', form.value.modelType, 'cvFolds:', form.value.cvFolds)
    const res = await api.trainModel(form.value.modelType, form.value.cvFolds)
    console.log('[Model] Training response:', res)
    trainingResult.value = res

    if (res.success) {
      progressPct.value = 100
      progressStage.value = '完成'
      progressMsg.value = '模型训练完成'
      ElMessage.success('模型训练完成: ' + (res.data?.best_model || ''))
      await loadResults()
    } else {
      ElMessage.error(res.message || '训练失败')
    }
  } catch (e) {
    console.error('[Model] Training error:', e)
    ElMessage.error('训练失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    trainingResult.value = {
      success: false,
      message: e.response?.data?.detail || e.message || '训练失败'
    }
  } finally {
    training.value = false
    progressPct.value = 0
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }
}

const stageLabel = (stage) => {
  const map = {
    loading: '加载数据',
    training: '训练中',
    done: '完成',
    error: '错误',
  }
  return map[stage] || stage || ''
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