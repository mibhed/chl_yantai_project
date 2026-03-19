<template>
  <div class="data-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>📥 数据导入</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="样本数据" name="samples">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleSampleChange"
            :limit="1"
            accept=".csv,.xlsx,.xls"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持CSV/Excel格式文件</div>
            </template>
          </el-upload>
          
          <div v-if="sampleFile" class="file-info">
            <p>已选择: {{ sampleFile.name }}</p>
            <el-button type="primary" @click="uploadSample" :loading="uploading">
              上传样本数据
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="卫星影像验证" name="validate">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleValidateChange"
            :limit="1"
            accept=".tif,.tiff"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽TIFF文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持MODIS、Landsat、Sentinel-2等卫星影像</div>
            </template>
          </el-upload>
          
          <div v-if="validateFile" class="file-info">
            <p>已选择: {{ validateFile.name }}</p>
            <el-button type="primary" @click="validateSatellite" :loading="validating">
              验证影像格式
            </el-button>
          </div>

          <el-card v-if="validationResult" class="validation-result">
            <template #header>
              <span>验证结果</span>
            </template>
            <el-alert
              :title="validationResult.valid ? '✓ 验证通过' : '✗ 验证失败'"
              :type="validationResult.valid ? 'success' : 'error'"
              show-icon
              :closable="false"
            />
            
            <el-descriptions :column="1" border class="validation-details">
              <el-descriptions-item label="卫星类型">
                {{ validationResult.satellite_type }}
              </el-descriptions-item>
            </el-descriptions>

            <div v-if="validationResult.errors && validationResult.errors.length" class="error-section">
              <h4>错误:</h4>
              <ul>
                <li v-for="(error, idx) in validationResult.errors" :key="idx">
                  {{ error }}
                </li>
              </ul>
            </div>

            <div v-if="validationResult.warnings && validationResult.warnings.length" class="warning-section">
              <h4>警告:</h4>
              <ul>
                <li v-for="(warning, idx) in validationResult.warnings" :key="idx">
                  {{ warning }}
                </li>
              </ul>
            </div>

            <div v-if="validationResult.suggestions && validationResult.suggestions.length" class="suggestion-section">
              <h4>建议:</h4>
              <ul>
                <li v-for="(suggestion, idx) in validationResult.suggestions" :key="idx">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="卫星影像转换" name="convert">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleConvertChange"
            :limit="1"
            accept=".tif,.tiff"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽TIFF文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">自动转换为标准格式，支持MODIS、Landsat、Sentinel-2</div>
            </template>
          </el-upload>
          
          <div v-if="convertFile" class="file-info">
            <p>已选择: {{ convertFile.name }}</p>
            
            <el-form :model="convertForm" label-width="120px" class="convert-form">
              <el-form-item label="卫星类型">
                <el-select v-model="convertForm.satellite_type" placeholder="自动识别" clearable>
                  <el-option label="自动识别" value="" />
                  <el-option label="MODIS" value="MODIS" />
                  <el-option label="Landsat" value="Landsat" />
                  <el-option label="Sentinel-2" value="Sentinel2" />
                </el-select>
              </el-form-item>
              
              <el-form-item label="目标分辨率">
                <el-input-number 
                  v-model="convertForm.target_resolution" 
                  :min="10" 
                  :max="1000" 
                  :step="10"
                  placeholder="保持原分辨率"
                />
                <span class="unit">米</span>
              </el-form-item>
              
              <el-form-item label="重采样方法">
                <el-select v-model="convertForm.resampling_method">
                  <el-option label="最近邻" value="nearest" />
                  <el-option label="双线性" value="bilinear" />
                  <el-option label="三次卷积" value="cubic" />
                </el-select>
              </el-form-item>
            </el-form>

            <el-button type="primary" @click="convertSatellite" :loading="converting">
              转换影像
            </el-button>
          </div>

          <el-card v-if="convertResult" class="convert-result">
            <template #header>
              <span>转换结果</span>
            </template>
            <el-alert
              :title="convertResult.success ? '✓ 转换成功' : '✗ 转换失败'"
              :type="convertResult.success ? 'success' : 'error'"
              show-icon
              :closable="false"
            />
            
            <div v-if="convertResult.success && convertResult.data" class="result-details">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="原始文件">
                  {{ convertResult.data.original_file }}
                </el-descriptions-item>
                <el-descriptions-item label="卫星类型">
                  {{ convertResult.data.satellite_type }}
                </el-descriptions-item>
                <el-descriptions-item label="影像尺寸">
                  {{ convertResult.data.shape }}
                </el-descriptions-item>
                <el-descriptions-item label="数据类型">
                  {{ convertResult.data.dtype }}
                </el-descriptions-item>
              </el-descriptions>
              
              <div class="download-section">
                <el-button type="success" @click="downloadConverted">
                  下载转换后的影像
                </el-button>
              </div>
            </div>
          </el-card>
        </el-tab-pane>

        <el-tab-pane label="卫星影像上传" name="tiff">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleTiffChange"
            :limit="1"
            accept=".tif,.tiff"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽TIFF文件到此处或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持GeoTIFF格式</div>
            </template>
          </el-upload>
          
          <div v-if="tiffFile" class="file-info">
            <p>已选择: {{ tiffFile.name }}</p>
            <el-button type="primary" @click="uploadTiff" :loading="uploadingTiff">
              上传卫星影像
            </el-button>
          </div>
        </el-tab-pane>

        <el-tab-pane label="MODIS L2 数据" name="modis">
          <el-alert
            title="数据来源说明"
            type="info"
            :closable="false"
            show-icon
            class="info-alert"
          >
            <template #default>
              <p style="margin: 8px 0; line-height: 1.6;">
                <strong>推荐数据源：</strong>NASA LAADS (<a href="https://ladsweb.modaps.eosdis.nasa.gov/" target="_blank">ladsweb.modaps.eosdis.nasa.gov</a>)
              </p>
              <p style="margin: 8px 0; line-height: 1.6;">
                选择产品：<strong>MODISA_L2</strong>（或 MYD21_L2），下载 <code>.nc</code> 或 <code>.hdf</code> 格式文件。
                L2 产品已包含大气校正后的遥感反射率（Rrs），可直接使用。
              </p>
              <p style="margin: 8px 0; line-height: 1.6;">
                <strong>研究区域：</strong>烟台近岸海域（经度 120.9°E~122.8°E，纬度 36.1°N~37.8°N）
              </p>
            </template>
          </el-alert>

          <el-card class="download-guide">
            <template #header>
              <span>下载步骤</span>
            </template>
            <ol class="guide-list">
              <li>访问 <a href="https://ladsweb.modaps.eosdis.nasa.gov/" target="_blank">NASA LAADS</a></li>
              <li>注册/登录账号</li>
              <li>选择产品：<code>MODISA_L2</code> 或 <code>MYD21_L2</code></li>
              <li>设置时间范围和区域（烟台近岸：120.9°E~122.8°E, 36.1°N~37.8°N）</li>
              <li>选择 <code>.nc</code> 或 <code>.hdf</code> 格式下载</li>
              <li>下载后直接上传至下方「开始反演」页签</li>
            </ol>
          </el-card>

          <el-card class="band-info">
            <template #header>
              <span>支持的 Rrs 波段</span>
            </template>
            <el-table :data="modisBandInfo" size="small" border>
              <el-table-column prop="name" label="波段" width="120" />
              <el-table-column prop="wavelength" label="中心波长(nm)" width="130" />
              <el-table-column prop="description" label="说明" />
            </el-table>
          </el-card>
        </el-tab-pane>
    </el-card>

    <el-card v-if="uploadResult" class="result-card">
      <template #header>
        <span>上传结果</span>
      </template>
      <el-alert
        :title="uploadResult.message"
        :type="uploadResult.success ? 'success' : 'error'"
        show-icon
      />
      <div v-if="uploadResult.success && uploadResult.data" class="result-details">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">
            {{ uploadResult.data.filename }}
          </el-descriptions-item>
          <el-descriptions-item label="数据行数" v-if="uploadResult.data.row_count">
            {{ uploadResult.data.row_count }}
          </el-descriptions-item>
          <el-descriptions-item label="列名" v-if="uploadResult.data.columns">
            {{ uploadResult.data.columns.join(', ') }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const activeTab = ref('validate')
const sampleFile = ref(null)
const tiffFile = ref(null)
const validateFile = ref(null)
const convertFile = ref(null)
const uploading = ref(false)
const uploadingTiff = ref(false)
const validating = ref(false)
const converting = ref(false)
const uploadResult = ref(null)
const validationResult = ref(null)
const convertResult = ref(null)
const convertForm = ref({
  satellite_type: '',
  target_resolution: null,
  resampling_method: 'nearest'
})

const modisBandInfo = ref([
  { name: 'Rrs_412', wavelength: 412, description: '蓝光波段1（气溶胶/沿海）' },
  { name: 'Rrs_443', wavelength: 443, description: '蓝光波段2（叶绿素吸收峰）' },
  { name: 'Rrs_469', wavelength: 469, description: '蓝光波段3' },
  { name: 'Rrs_488', wavelength: 488, description: '青光波段（散射峰）' },
  { name: 'Rrs_531', wavelength: 531, description: '绿光波段1（色素相关）' },
  { name: 'Rrs_547', wavelength: 547, description: '绿光波段2' },
  { name: 'Rrs_555', wavelength: 555, description: '绿光波段3（浮游植物峰）' },
  { name: 'Rrs_645', wavelength: 645, description: '红光波段1（Chl-a荧光）' },
  { name: 'Rrs_667', wavelength: 667, description: '红光波段2' },
  { name: 'Rrs_678', wavelength: 678, description: '红光波段3（Chl-a荧光峰）' },
])

const handleSampleChange = (file) => {
  sampleFile.value = file
}

const handleTiffChange = (file) => {
  tiffFile.value = file
}

const handleValidateChange = (file) => {
  validateFile.value = file
  validationResult.value = null
}

const handleConvertChange = (file) => {
  convertFile.value = file
  convertResult.value = null
}

const uploadSample = async () => {
  if (!sampleFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploading.value = true
  try {
    const res = await api.uploadSamples(sampleFile.value.raw)
    uploadResult.value = res
    if (res.success) {
      store.setSamplesUploaded(true)
      ElMessage.success('样本数据上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    console.error('Upload samples error:', e)
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    uploadResult.value = { success: false, message: e.message }
  } finally {
    uploading.value = false
  }
}

const uploadTiff = async () => {
  if (!tiffFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  uploadingTiff.value = true
  try {
    console.log('Uploading TIFF file:', tiffFile.value.name)
    const res = await api.uploadTiff(tiffFile.value.raw)
    console.log('Upload result:', res)
    uploadResult.value = res
    if (res.success) {
      store.setTiffUploaded(true)
      ElMessage.success('卫星影像上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    console.error('Upload TIFF error:', e)
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    uploadResult.value = { success: false, message: e.message }
  } finally {
    uploadingTiff.value = false
  }
}

const validateSatellite = async () => {
  if (!validateFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  validating.value = true
  validationResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', validateFile.value.raw)

    console.log('Validating satellite image:', validateFile.value.name)
    const res = await api.validateSatellite(formData)
    console.log('Validation result:', res)

    if (res.success) {
      validationResult.value = res.data
      ElMessage.success('影像验证完成')
    } else {
      ElMessage.error(res.message || '验证失败')
      validationResult.value = res.data || {
        valid: false,
        satellite_type: 'Unknown',
        errors: [res.message || '验证失败'],
        warnings: [],
        suggestions: []
      }
    }
  } catch (e) {
    console.error('Validation error:', e)
    ElMessage.error('验证失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    validationResult.value = {
      valid: false,
      satellite_type: 'Unknown',
      errors: [e.response?.data?.detail || e.message || '验证失败'],
      warnings: [],
      suggestions: ['请检查文件格式是否正确']
    }
  } finally {
    validating.value = false
  }
}

const convertSatellite = async () => {
  if (!convertFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }

  converting.value = true
  convertResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', convertFile.value.raw)
    formData.append('satellite_type', convertForm.value.satellite_type || '')
    if (convertForm.value.target_resolution) {
      formData.append('target_resolution', convertForm.value.target_resolution)
    }
    formData.append('resampling_method', convertForm.value.resampling_method)

    console.log('Converting satellite image:', convertFile.value.name)
    const res = await api.convertSatellite(formData)
    console.log('Conversion result:', res)

    convertResult.value = res

    if (res.success) {
      ElMessage.success('影像转换成功')
    } else {
      ElMessage.error(res.message || '转换失败')
    }
  } catch (e) {
    console.error('Conversion error:', e)
    ElMessage.error('转换失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
    convertResult.value = {
      success: false,
      message: e.response?.data?.detail || e.message || '转换失败'
    }
  } finally {
    converting.value = false
  }
}

const downloadConverted = () => {
  if (convertResult.value && convertResult.value.data && convertResult.value.data.download_url) {
    window.open(convertResult.value.data.download_url, '_blank')
  }
}
</script>

<style scoped>
.data-view {
  max-width: 1200px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.upload-demo {
  margin: 20px 0;
}

.file-info {
  margin-top: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.file-info p {
  margin-bottom: 15px;
}

.result-card {
  margin-top: 20px;
}

.result-details {
  margin-top: 15px;
}

.validation-result {
  margin-top: 20px;
}

.validation-details {
  margin-top: 15px;
}

.error-section {
  margin-top: 15px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
}

.error-section h4 {
  color: #f56c6c;
  margin-bottom: 10px;
}

.warning-section {
  margin-top: 15px;
  padding: 10px;
  background: #fdf6ec;
  border-radius: 4px;
}

.warning-section h4 {
  color: #e6a23c;
  margin-bottom: 10px;
}

.suggestion-section {
  margin-top: 15px;
  padding: 10px;
  background: #f0f9eb;
  border-radius: 4px;
}

.suggestion-section h4 {
  color: #67c23a;
  margin-bottom: 10px;
}

.error-section ul,
.warning-section ul,
.suggestion-section ul {
  margin: 0;
  padding-left: 20px;
}

.error-section li,
.warning-section li,
.suggestion-section li {
  margin-bottom: 5px;
}

.convert-form {
  margin-top: 20px;
  max-width: 600px;
}

.unit {
  margin-left: 10px;
  color: #909399;
}

.convert-result {
  margin-top: 20px;
}

.download-section {
  margin-top: 20px;
  text-align: center;
}

.info-alert {
  margin: 20px 0;
}

.download-guide {
  margin-bottom: 15px;
}

.guide-list {
  padding-left: 20px;
  line-height: 1.8;
  color: #606266;
}

.guide-list code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.band-info {
  margin-top: 10px;
}
</style>