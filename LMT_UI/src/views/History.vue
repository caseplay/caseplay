<template>
  <div class="page">
    <header class="page-top">
      <div>
        <span class="eyebrow">YOUR STORY ARCHIVE</span>
        <h1>我的演绎</h1>
        <p class="muted">每一次选择都有迹可循，随时继续未完的故事。</p>
      </div>
      <RouterLink class="primary-button" to="/">探索新故事 →</RouterLink>
    </header>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <div class="history-list">
      <article class="history-card" v-for="s in sessions" :key="s.id">
        <div class="history-icon">{{ s.status === "ended" ? "✓" : "↗" }}</div>
        <div>
          <span class="eyebrow"
            >{{ s.status === "ended" ? "已完成" : "进行中" }} ·
            {{ date(s.created_at) }}</span
          >
          <h3>{{ s.script_title }}</h3>
          <p class="muted">
            扮演 {{ s.character_name }} · {{ s.metrics.turns }} 轮行动 ·
            {{ s.metrics.evidence_count }} 条证据
          </p>
        </div>
        <RouterLink
          :to="(s.status === 'ended' ? '/report/' : '/play/') + s.id"
          class="secondary-button"
          >{{ s.status === "ended" ? "查看复盘" : "继续演绎" }} →</RouterLink
        >
      </article>
    </div>
    <div class="empty-state" v-if="!busy && !sessions.length">
      <h2>你的故事，从这里开始</h2>
      <p>选择一个感兴趣的情境，尝试从不同角色的角度思考。</p>
      <RouterLink class="primary-button" to="/">探索剧本</RouterLink>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";
const sessions = ref([]),
  error = ref(""),
  busy = ref(true);
const date = (s) => new Date(s).toLocaleDateString("zh-CN");
onMounted(async () => {
  try {
    sessions.value = await api("/history");
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
});
</script>
