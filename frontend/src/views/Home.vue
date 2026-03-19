<template>
  <div class="home-view">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="hero-card">
          <h2>欢迎使用叶绿素a遥感分析系统</h2>
          <p>基于卫星遥感的叶绿素a浓度反演与可视化分析平台</p>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="feature-cards">
      <el-col :span="6" v-for="feature in features" :key="feature.title">
        <el-card class="feature-card" @click="goTo(feature.path)">
          <div class="feature-icon">{{ feature.icon }}</div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <span>系统概览</span>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ regions.length }}</div>
                <div class="stat-label">分析区域</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ models.length }}</div>
                <div class="stat-label">可用模型</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">-</div>
                <div class="stat-label">样本数量</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-value">-</div>
                <div class="stat-label">分析次数</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()

const regions = computed(() => store.regions)
const models = computed(() => store.models)

const features = [
  {
    icon: '📥',
    title: '数据管理',
    description: '上传和管理样本数据、卫星影像',
    path: '/data'
  },
  {
    icon: '🤖',
    title: '模型训练',
    description: '训练和评估多种机器学习模型',
    path: '/model'
  },
  {
    icon: '🗺️',
    title: '空间分析',
    description: '生成叶绿素a空间分布图',
    path: '/analysis'
  },
  {
    icon: '📊',
    title: '结果展示',
    description: '查看分析结果和数据可视化',
    path: '/results'
  },
  {
    icon: '🛰️',
    title: '遥感反演',
    description: '上传MODIS L2数据直接反演Chl-a分布图',
    path: '/retrieval'
  }
]

const goTo = (path) => {
  router.push(path)
}

onMounted(async () => {
  await store.fetchRegions()
  await store.fetchModels()
})
</script>

<style scoped>
.home-view {
  max-width: 1400px;
  margin: 0 auto;
}

.hero-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 16px;
  text-align: center;
}

.hero-card h2 {
  margin: 0 0 10px 0;
  font-size: 32px;
}

.hero-card p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.feature-cards {
  margin: 30px 0;
}

.feature-card {
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
  height: 200px;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.feature-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.feature-card h3 {
  margin: 10px 0;
  color: #333;
}

.feature-card p {
  color: #666;
  font-size: 14px;
}

.stats-card .card-header {
  font-weight: bold;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  margin-top: 10px;
  color: #666;
}
</style>