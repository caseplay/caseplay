<template>
  <div class="script-detail-page">
    <div v-if="script" class="glass-panel detail-card">
      <button class="back-btn" @click="router.back()">❮ 返回</button>

      <div class="header">
        <h1>{{ script.title }}</h1>
        <p class="tagline">选择你的角色开始</p>
      </div>

      <div class="roles-grid">
        <div
          v-for="(role, index) in script.roles"
          :key="index"
          class="role-card"
          :class="{ selected: selectedRole === role }"
          @click="selectedRole = role"
        >
          <span class="role-icon">🎭</span>
          <h3>{{ role }}</h3>
        </div>
      </div>

      <div class="action-footer">
        <button
          class="start-btn"
          :disabled="!selectedRole || isLoading"
          @click="startGame"
        >
          {{ isLoading ? 'AI 初始化中...' : '开始推演' }}
        </button>
      </div>
    </div>
    <div v-else class="loading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const script = ref(null)
const selectedRole = ref(null)
const isLoading = ref(false)

const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/scripts/${route.params.id}`)
    script.value = res.data
  } catch (err) {
    console.error("Failed to fetch script:", err)
    router.push({ name: 'Home' })
  }
})

const startGame = async () => {
  if (!selectedRole.value) return
  isLoading.value = true

  try {
    const res = await axios.post(`${API_BASE}/play/start`, {
      token: localStorage.getItem('token'),
      script_id: script.value.id,
      character: selectedRole.value
    })

    // Pass initial scene via state
    localStorage.setItem('current_scene', JSON.stringify(res.data.scene))
    router.push({ name: 'Gameplay', params: { session_id: res.data.session_id } })
  } catch (err) {
    console.error("Failed to start game:", err)
    ElMessage.error(err.response?.data?.error || "推演启动失败。请确保后端已启动并且 模型 API Key 有效。")
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.script-detail-page {
  padding: 4rem 2rem;
  max-width: 900px;
  margin: 0 auto;
}

.detail-card {
  position: relative;
  padding: 4rem;
}

.back-btn {
  position: absolute;
  top: 2rem;
  left: 2rem;
  background: transparent;
  color: var(--text-muted);
}
.back-btn:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.header {
  text-align: center;
  margin-bottom: 3rem;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.role-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.role-card:hover {
  background: rgba(59, 130, 246, 0.1);
  transform: translateY(-5px);
}

.role-card.selected {
  background: rgba(59, 130, 246, 0.2);
  border-color: var(--primary);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.role-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.action-footer {
  text-align: center;
}

.start-btn {
  font-size: 1.2rem;
  padding: 1rem 3rem;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 50px;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}
.start-btn:hover:not(:disabled) {
  box-shadow: 0 6px 25px rgba(59, 130, 246, 0.6);
}

.loading {
  text-align: center;
  font-size: 1.5rem;
  color: var(--text-muted);
}
</style>
