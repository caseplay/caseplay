<template>
  <div class="profile-page">
    <div class="glass-panel profile-card">
      <div class="header">
        <h2>您的个人主页</h2>
        <p class="email">{{ user.email }}</p>
        <span v-if="user.is_admin" class="admin-badge">管理员</span>
      </div>

      <div class="stats-section">
        <div class="stat-box">
          <h3>剩余畅玩次数</h3>
          <div class="count" :class="{ empty: user.remaining_plays <= 0 }">
            {{ user.remaining_plays }}
          </div>
          <p class="hint" v-if="user.remaining_plays === 0">您的游玩次数已用尽，请联系管理员获取更多次数。</p>
        </div>
      </div>

      <div class="actions">
        <button v-if="user.is_admin" class="btn primary" @click="router.push('/admin')">进入后台管理</button>
        <button class="btn secondary" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const user = ref({ email: '', remaining_plays: 0, is_admin: false })
const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.error("请先登录")
    router.push('/login')
    return
  }

  try {
    const res = await axios.get(`${API_BASE}/auth/me?token=${token}`)
    user.value = res.data
  } catch (err) {
    ElMessage.error(err.response?.data?.error || "信息加载失败")
    if (err.response?.status === 401 || err.response?.status === 404) {
      handleLogout()
    }
  }
})

const handleLogout = () => {
  localStorage.removeItem('token')
  ElMessage.success("已安全退出")
  router.push('/login')
}
</script>

<style scoped>
.profile-page {
  padding: 4rem 2rem;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 65px);
}
.profile-card {
  width: 100%;
  max-width: 500px;
  padding: 3rem;
  text-align: center;
}
.header {
  margin-bottom: 3rem;
}
.header h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}
.email {
  color: var(--text-muted);
  font-size: 1.1rem;
}
.admin-badge {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.2rem 0.8rem;
  background: var(--primary);
  color: white;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}
.stats-section {
  display: flex;
  justify-content: center;
  margin-bottom: 3rem;
}
.stat-box {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
}
.stat-box h3 {
  margin-bottom: 1rem;
  color: var(--text-muted);
}
.count {
  font-size: 3rem;
  font-weight: bold;
  color: #34d399;
}
.count.empty {
  color: #ef4444;
}
.hint {
  font-size: 0.9rem;
  margin-top: 1rem;
  color: #ef4444;
}
.actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.btn {
  padding: 1rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
}
.btn.primary {
  background: var(--primary);
  color: white;
  border: none;
}
.btn.primary:hover {
  background: #2563eb;
}
.btn.secondary {
  background: transparent;
  color: #ef4444;
  border: 1px solid #ef4444;
}
.btn.secondary:hover {
  background: #ef4444;
  color: white;
}
</style>
