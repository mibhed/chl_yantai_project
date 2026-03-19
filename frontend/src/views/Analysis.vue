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
            <div class="stat-value">{{ analysisResult.data?.summary?.mean_chl_a?.toFixed(3) || 'N/A' }} mg/m³</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">最大叶绿素浓度</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.max_chl_a?.toFixed(3) || 'N/A' }} mg/m³</div>
          </div>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">最小叶绿素浓度</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.min_chl_a?.toFixed(3) || 'N/A' }} mg/m³</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="stat-item">
            <div class="stat-label">标准差</div>
            <div class="stat-value">{{ analysisResult.data?.summary?.std_chl_a?.toFixed(3) || 'N/A' }} mg/m³</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card v-if="monthlyResult" class="result-card">
      <template #header>
        <span>月度分析结果 - {{ monthlyResult.data?.region }} {{ monthlyResult.data?.year }}年</span>
      </template>
      <div ref="monthlyChartRef" class="chart-container"></div>
    </el-card>

    <el-card v-if="multiRegionResult" class="result-card">
      <template #header>
        <span>多区域对比结果 - {{ multiRegionResult.data?.year }}年</span>
      </template>
      <div ref="multiRegionChartRef" class="chart-container"></div>
    </el-card>

    <el-card v-if="multiYearResult" class="result-card">
      <template #header>
        <span>多年趋势分析结果 - {{ multiYearResult.data?.region }}</span>
      </template>
      <div ref="multiYearChartRef" class="chart-container"></div>
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
import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
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
const regions = computed(() => store.regions)
const models = computed(() => store.models)
const years = Array.from({ length: 8 }, (_, i) => 2018 + i)
const months = Array.from({ length: 12 }, (_, i) => i + 1)

const showMonthlyDialog = ref(false)
const showMultiRegionDialog = ref(false)
const showMultiYearDialog = ref(false)

const monthlyForm = ref({ region: '', year: new Date().getFullYear() })
const multiRegionForm = ref({ year: new Date().getFullYear() })
const multiYearForm = ref({ region: '', startYear: 2020, endYear: 2025 })

const monthlyResult = ref(null)
const multiRegionResult = ref(null)
const multiYearResult = ref(null)

const monthlyChartRef = ref(null)
const multiRegionChartRef = ref(null)
const multiYearChartRef = ref(null)

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
    ElMessage.error('分析失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const runMonthlyAnalysis = async () => {
  if (!monthlyForm.value.region) {
    ElMessage.warning('请选择区域')
    return
  }

  analyzing.value = true
  try {
    const res = await api.monthlyAnalysis(
      monthlyForm.value.region,
      monthlyForm.value.year,
      form.value.model
    )
    monthlyResult.value = res
    showMonthlyDialog.value = false
    if (res.success) {
      ElMessage.success('月度分析完成')
      await nextTick()
      renderMonthlyChart(res.data)
    } else {
      ElMessage.error(res.message || '月度分析失败')
    }
  } catch (e) {
    ElMessage.error('月度分析失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const runMultiRegionAnalysis = async () => {
  analyzing.value = true
  try {
    const res = await api.multiRegionAnalysis(
      multiRegionForm.value.year,
      form.value.model
    )
    multiRegionResult.value = res
    showMultiRegionDialog.value = false
    if (res.success) {
      ElMessage.success('多区域对比完成')
      await nextTick()
      renderMultiRegionChart(res.data)
    } else {
      ElMessage.error(res.message || '多区域对比失败')
    }
  } catch (e) {
    ElMessage.error('多区域对比失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const runMultiYearAnalysis = async () => {
  if (!multiYearForm.value.region) {
    ElMessage.warning('请选择区域')
    return
  }

  analyzing.value = true
  try {
    const res = await api.multiYearAnalysis(
      multiYearForm.value.region,
      multiYearForm.value.startYear,
      multiYearForm.value.endYear,
      form.value.model
    )
    multiYearResult.value = res
    showMultiYearDialog.value = false
    if (res.success) {
      ElMessage.success('多年趋势分析完成')
      await nextTick()
      renderMultiYearChart(res.data)
    } else {
      ElMessage.error(res.message || '多年趋势分析失败')
    }
  } catch (e) {
    ElMessage.error('多年趋势分析失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

const renderMonthlyChart = (data) => {
  if (!monthlyChartRef.value || !data.monthly_data) return

  const chart = echarts.init(monthlyChartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均叶绿素浓度'] },
    xAxis: {
      type: 'category',
      data: data.monthly_data.map(d => `${d.month}月`)
    },
    yAxis: {
      type: 'value',
      name: 'mg/m³',
      axisLabel: { formatter: '{value}' }
    },
    series: [{
      name: '平均叶绿素浓度',
      type: 'line',
      data: data.monthly_data.map(d => d.mean_chl_a),
      smooth: true,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#667eea' }
    }]
  }
  chart.setOption(option)
}

const renderMultiRegionChart = (data) => {
  if (!multiRegionChartRef.value || !data.multi_region_data) return

  const chart = echarts.init(multiRegionChartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均叶绿素浓度'] },
    xAxis: {
      type: 'category',
      data: data.multi_region_data.map(d => d.region),
      axisLabel: { rotate: 30 }
    },
    yAxis: {
      type: 'value',
      name: 'mg/m³'
    },
    series: [{
      name: '平均叶绿素浓度',
      type: 'bar',
      data: data.multi_region_data.map(d => d.mean_chl_a),
      itemStyle: { color: '#667eea' }
    }]
  }
  chart.setOption(option)
}

const renderMultiYearChart = (data) => {
  if (!multiYearChartRef.value || !data.multi_year_data) return

  const chart = echarts.init(multiYearChartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['平均叶绿素浓度'] },
    xAxis: {
      type: 'category',
      data: data.multi_year_data.map(d => `${d.year}年`)
    },
    yAxis: {
      type: 'value',
      name: 'mg/m³'
    },
    series: [{
      name: '平均叶绿素浓度',
      type: 'line',
      data: data.multi_year_data.map(d => d.mean_chl_a),
      smooth: true,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#764ba2' }
    }]
  }
  chart.setOption(option)
}

onMounted(async () => {
  await store.fetchRegions()
  await store.fetchModels()

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