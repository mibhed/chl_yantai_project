<template>
  <div class="analysis-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>🗺️ 空间分析</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="选择区域">
              <el-select v-model="form.region" placeholder="请选择区域">
                <el-option
                  v-for="region in regions"
                  :key="region.name"
                  :label="region.name"
                  :value="region.name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="选择年份">
              <el-select v-model="form.year" placeholder="请选择年份">
                <el-option
                  v-for="year in years"
                  :key="year"
                  :label="year"
                  :value="year"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="选择月份">
              <el-select v-model="form.month" placeholder="请选择月份">
                <el-option
                  v-for="month in months"
                  :key="month"
                  :label="`${month}月`"
                  :value="month"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="选择模型">
              <el-select v-model="form.model" placeholder="请选择模型">
                <el-option
                  v-for="model in models"
                  :key="model.id"
                  :label="`${model.name} (${model.id})`"
                  :value="model.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item>
              <el-button type="primary" @click="runAnalysis" :loading="analyzing">
                执行分析
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card v-if="analysisResult" class="result-card">
      <template #header>
        <span>分析结果</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">平均叶绿素浓度</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.mean?.toFixed(3) }} mg/m³</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">最大叶绿素浓度</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.max?.toFixed(3) }} mg/m³</div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">最小叶绿素浓度</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.min?.toFixed(3) }} mg/m³</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">标准差</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.std?.toFixed(3) }} mg/m³</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="chart-card">
      <template #header>
        <span>时间序列分析</span>
      </template>
      <el-button @click="showMonthlyDialog = true" type="primary">
        月度分析
      </el-button>
      <el-button @click="showMultiRegionDialog = true" type="primary">
        多区域对比
      </el-button>
      <el-button @click="showMultiYearDialog = true" type="primary">
        多年趋势
      </el-button>
    </el-card>

    <el-dialog v-model="showMonthlyDialog" title="月度分析" width="600px">
      <el-form :model="monthlyForm" label-width="100px">
        <el-form-item label="区域">
          <el-select v-model="monthlyForm.region">
            <el-option
              v-for="r in regions"
              :key="r.name"
              :label="r.name"
              :value="r.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="monthlyForm.year">
            <el-option
              v-for="y in years"
              :key="y"
              :label="y"
              :value="y"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMonthlyDialog = false">取消</el-button>
        <el-button type="primary" @click="runMonthlyAnalysis">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showMultiRegionDialog" title="多区域对比" width="600px">
      <el-form :model="multiRegionForm" label-width="100px">
        <el-form-item label="年份">
          <el-select v-model="multiRegionForm.year">
            <el-option
              v-for="y in years"
              :key="y"
              :label="y"
              :value="y"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMultiRegionDialog = false">取消</el-button>
        <el-button type="primary" @click="runMultiRegionAnalysis">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showMultiYearDialog" title="多年趋势分析" width="600px">
      <el-form :model="multiYearForm" label-width="100px">
        <el-form-item label="区域">
          <el-select v-model="multiYearForm.region">
            <el-option
              v-for="r in regions"
              :key="r.name"
              :label="r.name"
              :value="r.name"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开始年份">
          <el-input-number v-model="multiYearForm.startYear" :min="2018" :max="2025" />
        </el-form-item>
        <el-form-item label="结束年份">
          <el-input-number v-model="multiYearForm.endYear" :min="2018" :max="2025" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showMultiYearDialog = false">取消</el-button>
        <el-button type="primary" @click="runMultiYearAnalysis">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const form = ref({
  region: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  model: 'RF'
})
const analyzing = ref(false)
const analysisResult = ref(null)
const regions = ref([])
const models = ref([])
const years = Array.from({ length: 8 }, (_, i) => 2018 + i)
const months = Array.from({ length: 12 }, (_, i) => i + 1)

const showMonthlyDialog = ref(false)
const showMultiRegionDialog = ref(false)
const showMultiYearDialog = ref(false)

const monthlyForm = ref({ region: '', year: new Date().getFullYear() })
const multiRegionForm = ref({ year: new Date().getFullYear() })
const multiYearForm = ref({ region: '', startYear: 2020, endYear: 2025 })

const runAnalysis = async () => {
  if (!form.value.region) {
    ElMessage.warning('请选择区域')
    return
  }
  
  analyzing.value = true
  try {
    const res = await api.spatialAnalysis(
      form.value.region,
      form.value.year,
      form.value.month,
      form.value.model
    )
    analysisResult.value = res
    if (res.success) {
      ElMessage.success('空间分析完成')
    } else {
      ElMessage.error(res.message || '分析失败')
    }
  } catch (e) {
    ElMessage.error('分析失败: ' + e.message)
  } finally {
    analyzing.value = false
  }
}

const runMonthlyAnalysis = async () => {
  showMonthlyDialog.value = false
  ElMessage.info('月度分析功能开发中')
}

const runMultiRegionAnalysis = async () => {
  showMultiRegionDialog.value = false
  ElMessage.info('多区域对比功能开发中')
}

const runMultiYearAnalysis = async () => {
  showMultiYearDialog.value = false
  ElMessage.info('多年趋势分析功能开发中')
}

onMounted(async () => {
  await store.fetchRegions()
  await store.fetchModels()
  regions.value = store.regions
  models.value = store.models
  
  if (regions.value.length > 0) {
    form.value.region = regions.value[0].name
    monthlyForm.value.region = regions.value[0].name
    multiYearForm.value.region = regions.value[0].name
  }
})
</script>

<style scoped>
.analysis-view {
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

.chart-card {
  margin-top: 20px;
}

.stat-item {
  padding: 15px;
  text-align: center;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}
</style>