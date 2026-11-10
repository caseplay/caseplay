<template>
  <div class="report-page">
    <div class="report-actions">
      <button class="action-btn" @click="router.push('/home')">❮ 返回首页</button>
      <button class="action-btn primary" @click="printReport">🖨️ 打印报告</button>
    </div>

    <div v-if="reportData" class="a4-paper">
      <div class="paper-content">
        <div class="report-header">
          <h1>Caseplay</h1>
          <h2>法治教育鉴定报告</h2>
          <div class="meta-info">
            <span><strong>剧本：</strong> {{ reportData.script_title }}</span>
            <span><strong>扮演角色：</strong> {{ reportData.character_name }}</span>
            <span><strong>日期：</strong> {{ new Date(reportData.created_at).toLocaleDateString() }}</span>
          </div>
        </div>

        <div class="report-body">
          <h3>剧情评估与法理分析</h3>
          <p class="report-text" v-html="formattedReport"></p>
        </div>

        <div class="report-footer">
          <div class="signatures">
            <div class="sign-block">
              <p>AI 裁判长数字签名：</p>
              <p class="signature-font">Gemini 2.5 Flash</p>
            </div>
            <div class="sign-block stamp-container">
              <div class="red-stamp">
                <div class="stamp-inner">
                  <span class="star">★</span>
                  <span class="text">法治教育鉴定专用章</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="errorMsg" class="error-msg">
      {{ errorMsg }}
    </div>
    <div v-else class="loading">
      正在生成鉴定报告...
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const reportData = ref(null)
const errorMsg = ref('')

const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

const formattedReport = computed(() => {
  if (!reportData.value || !reportData.value.end_report) return ''
  let text = reportData.value.end_report
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\n/g, '<br>')
  return text
})

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/report/${route.params.session_id}`)
    reportData.value = res.data
  } catch (err) {
    console.error("Failed to fetch report:", err)
    errorMsg.value = "报告加载失败，请确保剧情已经完成。"
  }
})

const printReport = () => {
  window.print()
}
</script>

<style scoped>
.report-page {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
  min-height: calc(100vh - 65px);
}

.report-actions {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.action-btn {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  color: var(--text-main);
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}
.action-btn.primary {
  background: var(--primary);
  border: none;
}
.action-btn.primary:hover {
  background: var(--primary-hover);
}

/* A4 Paper Styling */
.a4-paper {
  background: #fff;
  color: #1a1a1a;
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  padding: 20mm;
  position: relative;
  border-radius: 4px;
}

.paper-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.report-header {
  text-align: center;
  border-bottom: 2px solid #b91c1c;
  padding-bottom: 2rem;
  margin-bottom: 2rem;
}

.report-header h1 {
  font-family: 'Times New Roman', serif;
  font-size: 2.5rem;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.report-header h2 {
  font-size: 1.5rem;
  color: #4a4a4a;
  margin-bottom: 1.5rem;
}

.meta-info {
  display: flex;
  justify-content: space-between;
  font-size: 1rem;
  font-family: 'Courier New', monospace;
  color: #333;
}

.report-body {
  flex: 1;
}

.report-body h3 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: #1a1a1a;
  border-left: 4px solid #b91c1c;
  padding-left: 0.8rem;
}

.report-text {
  font-size: 1.1rem;
  line-height: 1.8;
  white-space: pre-wrap;
  text-align: justify;
  font-family: 'Georgia', serif;
  color: #2a2a2a;
}

.report-footer {
  margin-top: 4rem;
  padding-top: 2rem;
}

.signatures {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.sign-block {
  text-align: center;
}

.signature-font {
  font-family: 'Brush Script MT', cursive;
  font-size: 2rem;
  color: #1e3a8a;
  margin-top: 1rem;
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.5rem;
}

/* Red Stamp CSS styling */
.stamp-container {
  position: relative;
}

.red-stamp {
  width: 140px;
  height: 140px;
  border: 4px solid #dc2626;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: rotate(-15deg);
  opacity: 0.85;
  pointer-events: none;
}

.stamp-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #dc2626;
  font-family: 'SimSun', serif; /* Traditional chinese font feel */
  font-weight: bold;
}

.stamp-inner .star {
  font-size: 2rem;
  margin-bottom: 0.2rem;
}

.stamp-inner .text {
  font-size: 1.1rem;
  text-align: center;
  letter-spacing: 2px;
}

.loading, .error-msg {
  text-align: center;
  font-size: 1.5rem;
  margin-top: 2rem;
}
.error-msg {
  color: #ef4444;
}

/* Print specific styles */
@media print {
  body * {
    visibility: hidden;
  }
  .a4-paper, .a4-paper * {
    visibility: visible;
  }
  .a4-paper {
    position: absolute;
    left: 0;
    top: 0;
    box-shadow: none;
    margin: 0;
    padding: 0;
    width: 100%;
  }
}
</style>
