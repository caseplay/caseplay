<template>
  <div class="gameplay-page">
    <div class="game-container glass-panel">
      <div class="scene-display" ref="sceneDisplayRef">
        <transition-group name="scene-anim" tag="div" class="history-list">
          <div v-for="(item, index) in history" :key="index" class="history-item" :class="item.role">
            <div class="avatar">{{ item.role === 'ai' ? '🎭' : '👤' }}</div>
            <div class="content">
              <!-- If User -->
              <div v-if="item.role === 'user'">{{ item.content }}</div>

              <!-- If AI -->
              <div v-else>
                <div class="narrator" v-if="item.content.narrator_text">
                  <i>{{ item.content.narrator_text }}</i>
                </div>

                <div v-if="item.content.npc_dialogues && item.content.npc_dialogues.length" class="npc-dialogues">
                  <div class="npc-line" v-for="(npc, idx) in item.content.npc_dialogues" :key="idx">
                    <strong>{{ npc.name }}:</strong> {{ npc.text }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </transition-group>
        <div v-if="isLoading" class="typing-indicator">
          <span>.</span><span>.</span><span>.</span>
        </div>
      </div>

      <div class="interaction-area" v-if="!isLoading && !isEnded">
        <h3>你打算怎么做？</h3>

        <div class="choices-grid" v-if="currentChoices.length">
          <button
            v-for="(choice, idx) in currentChoices"
            :key="idx"
            class="choice-btn"
            @click="submitAction(choice)"
          >
            {{ choice }}
          </button>
        </div>

        <div class="manual-input">
          <div class="separator" v-if="currentChoices.length"><span>或输入自定义行动</span></div>
          <form @submit.prevent="submitManualAction" class="input-form">
            <input
              v-model="manualInput"
              type="text"
              :disabled="isApiError"
              :placeholder="isApiError ? 'API额度不足，输入已禁用。' : '例如：我主动上前，反驳他的说法...'"
            />
            <button type="submit" :disabled="!manualInput.trim() || isApiError">发送</button>
          </form>
        </div>
      </div>

      <div class="interaction-area ended-area" v-if="isEnded">
        <h3>剧情推演已结束</h3>
        <p>本次演绎已结束。AI 已经生成了正式的法治教育鉴定报告。</p>
        <div class="end-actions" style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.5rem;">
          <button class="choice-btn return-btn" @click="router.push('/home')">返回首页</button>
          <button class="choice-btn primary return-btn" @click="router.push(`/report/${route.params.session_id}`)">📄 查看鉴定报告</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

const history = ref([])
const currentChoices = ref([])
const isLoading = ref(false)
const isEnded = ref(false)
const isApiError = ref(false)
const manualInput = ref('')
const sceneDisplayRef = ref(null)

const API_BASE = (import.meta.env.VITE_API_BASE || '/api')

onMounted(() => {
  const initialSceneStr = localStorage.getItem('current_scene')
  if (initialSceneStr) {
    const sceneInfo = JSON.parse(initialSceneStr)
    history.value.push({ role: 'ai', content: sceneInfo })
    currentChoices.value = sceneInfo.choices || []
    isEnded.value = sceneInfo.is_ended || false
    isApiError.value = sceneInfo.api_error || false
    localStorage.removeItem('current_scene')
  } else {
    history.value.push({ role: 'ai', content: { narrator_text: "会话已恢复。请输入你的下一步行动以继续。" } })
  }
})

const scrollToBottom = async () => {
  await nextTick()
  if (sceneDisplayRef.value) {
    sceneDisplayRef.value.scrollTop = sceneDisplayRef.value.scrollHeight
  }
}

const submitAction = async (actionText) => {
  if (!actionText.trim() || isLoading.value || isEnded.value) return

  history.value.push({ role: 'user', content: actionText })
  currentChoices.value = []
  isLoading.value = true
  manualInput.value = ''
  scrollToBottom()

  try {
    const res = await axios.post(`${API_BASE}/play/action`, {
      session_id: route.params.session_id,
      action: actionText
    })

    const sceneInfo = res.data.scene
    history.value.push({ role: 'ai', content: sceneInfo })
    currentChoices.value = sceneInfo.choices || []
    isEnded.value = sceneInfo.is_ended || false
    isApiError.value = sceneInfo.api_error || false
  } catch (err) {
    console.error("Action error:", err)
    history.value.push({ role: 'ai', content: { narrator_text: "生成下一幕时发生错误，请重试。" } })
    currentChoices.value = ["重试"]
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const submitManualAction = () => {
  submitAction(manualInput.value)
}
</script>

<style scoped>
.gameplay-page {
  padding: 2rem;
  height: calc(100vh - 65px);
  max-width: 1000px;
  margin: 0 auto;
}

.game-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.scene-display {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  scroll-behavior: smooth;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.history-item {
  display: flex;
  gap: 1rem;
  max-width: 85%;
}

.history-item.ai {
  align-self: flex-start;
}

.history-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.avatar {
  font-size: 2rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  flex-shrink: 0;
}

.content {
  background: rgba(0, 0, 0, 0.2);
  padding: 1rem 1.5rem;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 1.1rem;
  white-space: pre-wrap;
}

.history-item.ai .content {
  border-top-left-radius: 4px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.history-item.user .content {
  border-top-right-radius: 4px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.narrator {
  color: var(--text-muted);
  margin-bottom: 0.8rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.npc-dialogues {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.npc-line {
  margin-bottom: 0.5rem;
}
.npc-line strong {
  color: #c084fc;
}

.end-report {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  border-radius: 8px;
}
.end-report h4 {
  color: #f8fafc;
  margin-bottom: 0.5rem;
}

.interaction-area {
  padding: 2rem;
  background: rgba(15, 23, 42, 0.9);
  border-top: 1px solid var(--border);
}

.interaction-area h3 {
  margin-bottom: 1rem;
  color: var(--text-muted);
  font-size: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.choices-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.8rem;
  margin-bottom: 1.5rem;
}

.choice-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  text-align: left;
  padding: 1rem;
  font-size: 1rem;
  transition: all 0.2s;
  border-radius: 8px;
}

.choice-btn:hover {
  background: rgba(59, 130, 246, 0.15);
  border-color: var(--primary);
  transform: translateX(5px);
}

.return-btn {
  text-align: center;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border: none;
  font-weight: bold;
}
.return-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}

.separator {
  position: relative;
  text-align: center;
  margin: 1.5rem 0;
}
.separator::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 1px dashed var(--border);
  z-index: 0;
}
.separator span {
  background: #0f172a;
  padding: 0 1rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  position: relative;
  z-index: 1;
}

.input-form {
  display: flex;
  gap: 1rem;
}
.input-form input {
  margin-bottom: 0;
}

.scene-anim-enter-active,
.scene-anim-leave-active {
  transition: all 0.4s ease;
}
.scene-anim-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.2rem;
  padding: 1rem;
  font-size: 2rem;
  color: var(--primary);
}
.typing-indicator span {
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
