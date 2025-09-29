import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Analyze from '../views/Analyze.vue'
import Register from '../views/Register.vue'

// ルート定義
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/analyze',
    name: 'Analyze',
    component: Analyze,
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
  },
]

//ルーターインスタンス生成
const router = createRouter({ history: createWebHistory(), routes })

// ルーターエクスポート
export default router
