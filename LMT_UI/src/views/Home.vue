<template>
  <div class="home-page">
    <div class="header">
      <h1>探索剧本</h1>
      <p>选择一个剧本，开启您的 Caseplay 普法旅程。</p>
    </div>

    <div class="carousel-container" v-if="scripts.length">
      <button class="nav-btn prev" @click="prev">❮</button>

      <div class="carousel-track-wrapper" ref="carouselWrapper">
        <div class="carousel-track">
          <div class="carousel-item" v-for="script in scripts" :key="script.id">
            <div class="script-card glass-panel" @click="goToScript(script.id)">
              <div class="card-image-placeholder">
                <span class="icon">📜</span>
              </div>
              <div class="card-content">
                <h3>{{ script.title }}</h3>
                <p>点击查看详情并开启剧情</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <button class="nav-btn next" @click="next">❯</button>
    </div>
    <div v-else class="loading">剧本加载中...</div>

    <!-- History Section -->
    <div class="history-section" v-if="history.length">
      <div class="header">
        <h2>您的旅程记录</h2>
        <p>回顾您过去的剧情演绎与法治教育报告。</p>
      </div>

      <div class="history-grid">
        <div class="history-card glass-panel" v-for="session in history" :key="session.id">
          <div class="card-meta">
            <span class="status-badge" :class="session.status">{{ session.status.toUpperCase() }}</span>
            <span class="date">{{ new Date(session.created_at).toLocaleDateString() }}</span>
          </div>
          <h3>{{ session.script_title }}</h3>
          <p class="role-played">扮演角色：<strong>{{ session.character_name }}</strong></p>

          <div v-if="session.status === 'ended'" class="ongoing-notice">
            <button class="resume-btn" style="border-color: #34d399; color: #34d399;" @click="router.push(`/report/${session.id}`)">📄 查看法治鉴定报告</button>
          </div>

          <div v-if="session.status === 'ongoing'" class="ongoing-notice">
            <button class="resume-btn" @click="resumeSession(session.id)">继续演绎</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const scripts = ref([])
const history = ref([])
const carouselWrapper = ref(null)
const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/scripts`)
    scripts.value = res.data
  } catch (err) {
    console.error("Failed to fetch scripts:", err)
  }

  try {
    const token = localStorage.getItem('token')
    if (token) {
      const histRes = await axios.get(`${API_BASE}/history?token=${token}`)
      history.value = histRes.data
    }
  } catch (err) {
    console.error("Failed to fetch history:", err)
  }
})

const next = () => {
  if (carouselWrapper.value) {
    carouselWrapper.value.scrollBy({ left: carouselWrapper.value.clientWidth, behavior: 'smooth' })
  }
}

const prev = () => {
  if (carouselWrapper.value) {
    carouselWrapper.value.scrollBy({ left: -carouselWrapper.value.clientWidth, behavior: 'smooth' })
  }
}

const goToScript = (id) => {
  router.push({ name: 'ScriptDetail', params: { id } })
}

const resumeSession = (session_id) => {
  router.push({ name: 'Gameplay', params: { session_id } })
}
</script>

<style scoped>
.home-page {
  padding: 4rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 4rem;
}

.header h1, .header h2 {
  background: linear-gradient(135deg, #f8fafc, #94a3b8);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 1rem;
}
.header h1 { font-size: 3rem; }
.header h2 { font-size: 2.5rem; margin-top: 4rem; }

.carousel-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-btn {
  background: var(--panel-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border);
  border-radius: 50%;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  cursor: pointer;
  z-index: 10;
  color: var(--text-main);
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: var(--primary);
  transform: scale(1.1);
}

.carousel-track-wrapper {
  flex: 1;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scroll-behavior: smooth;
  border-radius: 20px;
  scrollbar-width: none;
}
.carousel-track-wrapper::-webkit-scrollbar {
  display: none;
}

.carousel-track {
  display: flex;
}

.carousel-item {
  min-width: 100%;
  scroll-snap-align: center;
  padding: 1rem;
}

.script-card {
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.script-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(59, 130, 246, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.card-image-placeholder {
  font-size: 5rem;
  margin-bottom: 2rem;
}

.loading {
  text-align: center;
  font-size: 1.5rem;
  color: var(--text-muted);
}

/* History Section */
.history-section {
  margin-top: 2rem;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 2rem;
}

.history-card {
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status-badge {
  font-size: 0.8rem;
  font-weight: bold;
  padding: 0.3rem 0.6rem;
  border-radius: 50px;
}
.status-badge.ongoing {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.4);
}
.status-badge.ended {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.date {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.role-played {
  color: var(--text-muted);
  margin-top: 0.5rem;
  margin-bottom: 1rem;
}
.role-played strong {
  color: #c084fc;
}

.report-block {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #e2e8f0;
}

.report-block h4 {
  color: #ddd6fe;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ongoing-notice {
  margin-top: 1.5rem;
  text-align: center;
}

.resume-btn {
  width: 100%;
  padding: 0.8rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--primary);
  color: var(--primary);
}
.resume-btn:hover {
  background: var(--primary);
  color: white;
}
</style>
