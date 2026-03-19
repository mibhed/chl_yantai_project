<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-left">
        <h1>🌊 叶绿素a遥感分析系统</h1>
      </div>
      <div class="header-right">
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          :ellipsis="false"
          @select="handleMenuSelect"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/data">数据管理</el-menu-item>
          <el-menu-item index="/model">模型训练</el-menu-item>
          <el-menu-item index="/analysis">空间分析</el-menu-item>
          <el-menu-item index="/results">结果展示</el-menu-item>
          <el-menu-item index="/retrieval">遥感反演</el-menu-item>
        </el-menu>
      </div>
    </el-header>
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

const handleMenuSelect = (index) => {
  router.push(index)
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-left h1 {
  color: white;
  margin: 0;
  font-size: 24px;
}

.header-right .el-menu {
  background: transparent;
  border: none;
}

.header-right .el-menu-item {
  color: rgba(255,255,255,0.8) !important;
}

.header-right .el-menu-item:hover,
.header-right .el-menu-item.is-active {
  background: rgba(255,255,255,0.2) !important;
  color: white !important;
}

.app-main {
  background: #f5f7fa;
  padding: 20px;
}
</style>