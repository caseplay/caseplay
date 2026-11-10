import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import ScriptDetail from '../views/ScriptDetail.vue'
import Gameplay from '../views/Gameplay.vue'
import Report from '../views/Report.vue'

import Profile from '../views/Profile.vue'
import Admin from '../views/Admin.vue'

const routes = [
  { path: '/', name: 'Home', component: Home, alias: '/home' },
  { path: '/login', name: 'Login', component: Login },
  { path: '/script/:id', name: 'ScriptDetail', component: ScriptDetail },
  { path: '/play/:session_id', name: 'Gameplay', component: Gameplay },
  { path: '/report/:session_id', name: 'Report', component: Report },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/admin', name: 'Admin', component: Admin }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Simple route guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.name !== 'Login' && !token) {
    next({ name: 'Login' })
  } else {
    next()
  }
})

export default router
