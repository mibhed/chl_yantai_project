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

        <el-tab-pane label="卫星影像" name="tiff">
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
      </el-tabs>
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
const activeTab = ref('samples')
const sampleFile = ref(null)
const tiffFile = ref(null)
const uploading = ref(false)
const uploadingTiff = ref(false)
const uploadResult = ref(null)

const handleSampleChange = (file) => {
  sampleFile.value = file
}

const handleTiffChange = (file) => {
  tiffFile.value = file
}

const uploadSample = async () => {
  if (!sampleFile.value) return
  
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
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploading.value = false
  }
}

const uploadTiff = async () => {
  if (!tiffFile.value) return
  
  uploadingTiff.value = true
  try {
    const res = await api.uploadTiff(tiffFile.value.raw)
    uploadResult.value = res
    if (res.success) {
      store.setTiffUploaded(true)
      ElMessage.success('卫星影像上传成功')
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (e) {
    ElMessage.error('上传失败: ' + e.message)
  } finally {
    uploadingTiff.value = false
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
</style>