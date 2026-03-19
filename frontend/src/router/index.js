import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/data',
    name: 'Data',
    component: () => import('@/views/Data.vue'),
    meta: { title: '数据管理' }
  },
  {
    path: '/model',
    name: 'Model',
    component: () => import('@/views/Model.vue'),
    meta: { title: '模型训练' }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/Analysis.vue'),
    meta: { title: '空间分析' }
  },
  {
    path: '/results',
    name: 'Results',
    component: () => import('@/views/Results.vue'),
    meta: { title: '结果展示' }
  },
  {
    path: '/retrieval',
    name: 'Retrieval',
    component: () => import('@/views/Retrieval.vue'),
    meta: { title: '遥感反演' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title} - 叶绿素a遥感分析系统`
  next()
})

export default router