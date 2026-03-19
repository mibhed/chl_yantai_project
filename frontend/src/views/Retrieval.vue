<template>
  <div class="retrieval-view">
    <el-row :gutter="20">
      <!-- 左侧：参数配置 -->
      <el-col :span="8">
        <el-card class="config-card">
          <template #header>
            <div class="card-header">
              <span>📡 叶绿素a遥感反演</span>
            </div>
          </template>

          <el-alert
            title="操作说明"
            type="info"
            :closable="false"
            show-icon
            class="guide-alert"
          >
            <template #default>
              <ol style="padding-left: 18px; margin: 6px 0; line-height: 1.8;">
                <li>上传 MODIS L2 数据文件 (.nc/.hdf)</li>
                <li>设置研究区域和模型参数</li>
                <li>点击「开始反演」</li>
                <li>查看统计结果并下载 Chl-a 分布图</li>
              </ol>
            </template>
          </el-alert>

          <el-divider content-position="left">1. 上传 MODIS L2 文件</el-divider>

          <el-upload
            class="upload-modis"
            drag
            :auto-upload="false"
            :on-change="handleModisChange"
            :limit="1"
            accept=".nc,.hdf,.h5,.hdf4"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽 .nc/.hdf 文件或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 NASA MODIS L2 NetCDF/HDF5 格式
              </div>
            </template>
          </el-upload>

          <div v-if="modisFile" class="file-info">
            <el-tag type="primary" size="large">
              已选择: {{ modisFile.name }}
            </el-tag>
          </div>

          <el-divider content-position="left">2. 研究区域（烟台近岸）</el-divider>

          <el-form :model="regionForm" label-width="80px" size="small">
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="经度范围">
                  <el-input-number
                    v-model="regionForm.lon_min"
                    :min="120" :max="123" :step="0.1"
                    placeholder="最小经度"
                    style="width: 100%;"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="至">
                  <el-input-number
                    v-model="regionForm.lon_max"
                    :min="120" :max="123" :step="0.1"
                    placeholder="最大经度"
                    style="width: 100%;"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="纬度范围">
                  <el-input-number
                    v-model="regionForm.lat_min"
                    :min="35" :max="39" :step="0.1"
                    placeholder="最小纬度"
                    style="width: 100%;"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="至">
                  <el-input-number
                    v-model="regionForm.lat_max"
                    :min="35" :max="39" :step="0.1"
                    placeholder="最大纬度"
                    style="width: 100%;"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <el-button link type="primary" size="small" @click="resetToYantai">
            恢复默认烟台近岸范围
          </el-button>

          <el-divider content-position="left">3. 模型参数</el-divider>

          <el-form :model="modelForm" label-width="80px" size="small">
            <el-form-item label="模型类型">
              <el-select v-model="modelForm.model_type" style="width: 100%;">
                <el-option label="随机森林 (RF)" value="RF" />
                <el-option label="极端随机树 (ET)" value="ET" />
                <el-option label="XGBoost (XGB)" value="XGB" />
                <el-option label="LightGBM (LGB)" value="LGB" />
                <el-option label="多元线性回归 (MLR)" value="MLR" />
                <el-option label="高斯过程 (GP)" value="GP" />
              </el-select>
            </el-form-item>
            <el-form-item label="质量过滤">
              <el-select v-model="modelForm.qa_max" style="width: 100%;">
                <el-option label="最佳像元 (QA=0)" :value="0" />
                <el-option label="良好+最佳 (QA≤1)" :value="1" />
                <el-option label="所有有效 (QA≤2)" :value="2" />
              </el-select>
            </el-form-item>
            <el-form-item label="训练数据">
              <el-switch
                v-model="modelForm.use_synthetic"
                active-text="合成数据"
                inactive-text="实测数据"
              />
            </el-form-item>
          </el-form>

          <el-divider />

          <el-button
            type="primary"
            size="large"
            style="width: 100%;"
            :loading="retrieving"
            :disabled="!modisFile"
            @click="runRetrieval"
          >
            {{ retrieving ? '反演中...' : '🚀 开始反演' }}
          </el-button>

          <div v-if="!modisFile" class="no-file-hint">
            请先上传 MODIS L2 文件
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：结果展示 -->
      <el-col :span="16">
        <!-- 读取结果 -->
        <el-card v-if="readResult" class="result-card">
          <template #header>
            <span>📊 MODIS L2 文件预览</span>
          </template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="文件名">
              {{ readResult.filename }}
            </el-descriptions-item>
            <el-descriptions-item label="文件格式">
              {{ readResult.file_format }}
            </el-descriptions-item>
            <el-descriptions-item label="影像尺寸">
              {{ readResult.shape ? readResult.shape.join(' × ') : '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="Rrs 波段数">
              {{ readResult.n_bands }}/10
            </el-descriptions-item>
            <el-descriptions-item label="经度范围">
              <span v-if="readResult.lon_range">
                {{ readResult.lon_range[0].toFixed(4) }}° ~ {{ readResult.lon_range[1].toFixed(4) }}°E
              </span>
              <span v-else>未知</span>
            </el-descriptions-item>
            <el-descriptions-item label="纬度范围">
              <span v-if="readResult.lat_range">
                {{ readResult.lat_range[0].toFixed(4) }}° ~ {{ readResult.lat_range[1].toFixed(4) }}°N
              </span>
              <span v-else>未知</span>
            </el-descriptions-item>
            <el-descriptions-item label="质量标志">
              {{ readResult.qa_available ? '✅ 可用' : '⚠️ 不可用' }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider content-position="left">Rrs 波段统计</el-divider>
          <el-table :data="bandStatsTable" size="small" stripe border max-height="300">
            <el-table-column prop="band" label="波段" width="90" />
            <el-table-column prop="mean" label="均值" width="100">
              <template #default="{ row }">
                {{ row.mean?.toFixed(5) }}
              </template>
            </el-table-column>
            <el-table-column prop="min" label="最小值" width="100">
              <template #default="{ row }">
                {{ row.min?.toFixed(5) }}
              </template>
            </el-table-column>
            <el-table-column prop="max" label="最大值" width="100">
              <template #default="{ row }">
                {{ row.max?.toFixed(5) }}
              </template>
            </el-table-column>
            <el-table-column prop="coverage" label="覆盖率(%)" width="100" />
          </el-table>

          <div v-if="readResult.warnings?.length" class="warnings-section">
            <el-alert
              v-for="(w, i) in readResult.warnings"
              :key="i"
              :title="w"
              type="warning"
              show-icon
              :closable="false"
              style="margin-top: 8px;"
            />
          </div>
        </el-card>

        <!-- 反演结果 -->
        <el-card v-if="retrievalResult" class="result-card">
          <template #header>
            <span>🌊 叶绿素a反演结果</span>
          </template>

          <el-alert
            :title="retrievalResult.success ? '✅ 反演成功' : '❌ 反演失败'"
            :type="retrievalResult.success ? 'success' : 'error'"
            show-icon
            :closable="false"
          />

          <div v-if="retrievalResult.success && retrievalResult.data">
            <!-- 统计信息 -->
            <el-row :gutter="16" class="stats-row" v-if="retrievalResult.data.statistics">
              <el-col :span="8">
                <div class="stat-box blue">
                  <div class="stat-value">
                    {{ retrievalResult.data.statistics.mean?.toFixed(3) }}
                  </div>
                  <div class="stat-label">平均 Chl-a (mg/m³)</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-box green">
                  <div class="stat-value">
                    {{ retrievalResult.data.statistics.min?.toFixed(3) }}
                    ~
                    {{ retrievalResult.data.statistics.max?.toFixed(3) }}
                  </div>
                  <div class="stat-label">Chl-a 范围 (mg/m³)</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-box purple">
                  <div class="stat-value">
                    {{ retrievalResult.data.statistics.valid_pixels }}
                  </div>
                  <div class="stat-label">
                    有效像元 ({{ retrievalResult.data.statistics.coverage }}%)
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-row :gutter="16" class="stats-row">
              <el-col :span="8">
                <div class="stat-box orange">
                  <div class="stat-value">
                    {{ retrievalResult.data.statistics?.median?.toFixed(3) }}
                  </div>
                  <div class="stat-label">中位数 (mg/m³)</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-box teal">
                  <div class="stat-value">
                    {{ retrievalResult.data.statistics?.std?.toFixed(3) }}
                  </div>
                  <div class="stat-label">标准差</div>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="stat-box gray">
                  <div class="stat-value">
                    {{ retrievalResult.data.model_type }} /
                    {{ retrievalResult.data.satellite_type }}
                  </div>
                  <div class="stat-label">模型 / 卫星</div>
                </div>
              </el-col>
            </el-row>

            <!-- 分位数 -->
            <el-descriptions
              v-if="retrievalResult.data.statistics"
              title="统计详情"
              :column="3"
              border
              size="small"
              style="margin-top: 16px;"
            >
              <el-descriptions-item label="25%分位数">
                {{ retrievalResult.data.statistics.p25?.toFixed(4) }}
              </el-descriptions-item>
              <el-descriptions-item label="75%分位数">
                {{ retrievalResult.data.statistics.p75?.toFixed(4) }}
              </el-descriptions-item>
              <el-descriptions-item label="影像尺寸">
                {{ retrievalResult.data.chl_a_shape?.join(' × ') }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 预览图 -->
            <div v-if="previewUrl" class="preview-section">
              <el-divider content-position="left">Chl-a 分布图预览</el-divider>
              <div class="preview-container">
                <img :src="previewUrl" alt="Chl-a 分布图" class="chl-preview" />
              </div>
            </div>

            <!-- 下载按钮 -->
            <div class="download-section">
              <el-button
                v-if="retrievalResult.data.tiff_path"
                type="success"
                size="large"
                @click="downloadResult('tiff')"
              >
                📥 下载 GeoTIFF (Chl-a 分布图)
              </el-button>
              <el-button
                v-if="retrievalResult.data.preview_path"
                type="primary"
                size="large"
                @click="downloadResult('png')"
              >
                🖼️ 下载 PNG 预览图
              </el-button>
            </div>
          </div>

          <div v-else-if="retrievalResult.message" class="error-detail">
            <el-alert
              :title="retrievalResult.message"
              type="error"
              show-icon
              :closable="false"
            />
          </div>
        </el-card>

        <!-- 空状态 -->
        <el-card v-if="!readResult && !retrievalResult" class="empty-card">
          <el-empty description="请上传 MODIS L2 文件开始反演">
            <el-button type="primary" @click="activeTab = 'modis'">
              查看数据上传说明
            </el-button>
          </el-empty>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()

const modisFile = ref(null)
const readResult = ref(null)
const retrievalResult = ref(null)
const retrieving = ref(false)
const previewUrl = ref(null)

const regionForm = ref({
  lon_min: 120.9,
  lon_max: 122.8,
  lat_min: 36.1,
  lat_max: 37.8,
})

const modelForm = ref({
  model_type: 'RF',
  qa_max: 1,
  use_synthetic: true,
})

const bandStatsTable = computed(() => {
  if (!readResult.value?.band_stats) return []
  return Object.entries(readResult.value.band_stats).map(([band, stats]) => ({
    band,
    ...stats,
  }))
})

const resetToYantai = () => {
  regionForm.value = {
    lon_min: 120.9,
    lon_max: 122.8,
    lat_min: 36.1,
    lat_max: 37.8,
  }
}

const handleModisChange = (file) => {
  modisFile.value = file
  readResult.value = null
  retrievalResult.value = null
  previewUrl.value = null

  // 自动读取文件元数据
  previewModis(file)
}

const previewModis = async (file) => {
  if (!file) return

  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('qa_max', modelForm.value.qa_max)

    if (regionForm.value.lon_min && regionForm.value.lon_max) {
      formData.append('lon_min', regionForm.value.lon_min)
      formData.append('lon_max', regionForm.value.lon_max)
      formData.append('lat_min', regionForm.value.lat_min)
      formData.append('lat_max', regionForm.value.lat_max)
    }

    const res = await api.readModisL2(formData)
    if (res.success) {
      readResult.value = res.data
      ElMessage.success('MODIS L2 文件读取成功')
    } else {
      ElMessage.warning(res.message || '文件读取异常')
    }
  } catch (e) {
    console.error('Read error:', e)
    ElMessage.error('文件读取失败: ' + (e.message || '未知错误'))
  }
}

const runRetrieval = async () => {
  if (!modisFile.value) {
    ElMessage.warning('请先上传 MODIS L2 文件')
    return
  }

  retrieving.value = true
  retrievalResult.value = null
  previewUrl.value = null

  try {
    const formData = new FormData()
    formData.append('file', modisFile.value.raw)
    formData.append('model_type', modelForm.value.model_type)
    formData.append('qa_max', modelForm.value.qa_max)
    formData.append('use_synthetic_model', modelForm.value.use_synthetic)
    formData.append('satellite_type', 'MODIS')

    if (regionForm.value.lon_min && regionForm.value.lon_max) {
      formData.append('lon_min', regionForm.value.lon_min)
      formData.append('lon_max', regionForm.value.lon_max)
      formData.append('lat_min', regionForm.value.lat_min)
      formData.append('lat_max', regionForm.value.lat_max)
    }

    ElMessage.info('正在反演，请稍候（大文件可能需要1-3分钟）...')

    const res = await api.chlaRetrieve(formData)
    retrievalResult.value = res

    if (res.success) {
      ElMessage.success('反演完成！')

      // 获取预览图 URL
      if (res.data?.preview_path) {
        previewUrl.value = `/api/modis/download/${res.data.preview_path}?t=${Date.now()}`
      }
    } else {
      ElMessage.error(res.message || '反演失败')
    }
  } catch (e) {
    console.error('Retrieval error:', e)
    ElMessage.error('反演失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    retrievalResult.value = {
      success: false,
      message: e.response?.data?.detail || e.message,
    }
  } finally {
    retrieving.value = false
  }
}

const downloadResult = (type) => {
  const filename = type === 'tiff'
    ? retrievalResult.value?.data?.tiff_path
    : retrievalResult.value?.data?.preview_path

  if (!filename) {
    ElMessage.warning('文件路径不存在')
    return
  }

  window.open(`/api/modis/download/${filename}`, '_blank')
}

onMounted(async () => {
  await store.fetchRegions()
  await store.fetchModels()
})
</script>

<style scoped>
.retrieval-view {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}

.config-card {
  position: sticky;
  top: 20px;
}

.guide-alert {
  margin-bottom: 10px;
}

.upload-modis {
  margin: 10px 0;
}

.file-info {
  margin: 10px 0;
  text-align: center;
}

.no-file-hint {
  text-align: center;
  color: #909399;
  margin-top: 10px;
  font-size: 13px;
}

.result-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-top: 16px;
}

.stat-box {
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  color: white;
}

.stat-box.blue { background: linear-gradient(135deg, #667eea, #764ba2); }
.stat-box.green { background: linear-gradient(135deg, #11998e, #38ef7d); }
.stat-box.purple { background: linear-gradient(135deg, #a855f7, #ec4899); }
.stat-box.orange { background: linear-gradient(135deg, #f093fb, #f5576c); }
.stat-box.teal { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.stat-box.gray { background: linear-gradient(135deg, #667eea, #764ba2); opacity: 0.8; }

.stat-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
}

.preview-section {
  margin-top: 20px;
}

.preview-container {
  text-align: center;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 10px;
}

.chl-preview {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.download-section {
  margin-top: 20px;
  text-align: center;
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.warnings-section {
  margin-top: 12px;
}

.empty-card {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-detail {
  margin-top: 16px;
}
</style>
