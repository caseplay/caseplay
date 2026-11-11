<template>
  <div class="page">
    <header class="page-top">
      <div>
        <span class="eyebrow">LEARNING AT YOUR OWN PACE</span>
        <h1>学习档案</h1>
        <p class="muted">用真实的行动记录，观察自己的学习过程。</p>
      </div>
    </header>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <template v-if="data"
      ><section class="profile-banner">
        <div class="avatar large">
          {{ account.user?.display_name?.slice(0, 1) }}
        </div>
        <div>
          <h2>{{ account.user?.display_name }}</h2>
          <p>{{ account.user?.email }}</p>
        </div>
        <span class="tag">情境探索者</span>
      </section>
      <div class="stats-grid">
        <div
          class="stat-card"
          v-for="(n, i) in [
            data.total_sessions,
            data.completed,
            data.evidence_count,
            data.reflection_count,
          ]"
          :key="i"
        >
          <span>{{
            ["参与演绎", "完成故事", "累计呈递线索", "保存复盘"][i]
          }}</span
          ><strong>{{ n }}</strong
          ><small>{{
            ["次真实会话", "次完整经历", "条，按各次演绎累计", "篇个人思考"][i]
          }}</small>
        </div>
      </div>
      <section class="panel">
        <div class="section-heading">
          <h2>最近的足迹</h2>
          <RouterLink to="/history">全部记录 →</RouterLink>
        </div>
        <article class="history-card" v-for="s in data.recent" :key="s.id">
          <div>
            <h3>{{ s.script_title }}</h3>
            <p class="muted">
              {{ s.character_name }} · {{ s.metrics.turns }} 轮行动
            </p>
          </div>
          <RouterLink
            class="secondary-button"
            :to="(s.status === 'ended' ? '/report/' : '/play/') + s.id"
            >{{ s.status === "ended" ? "查看复盘" : "继续演绎" }}</RouterLink
          >
        </article>
        <p v-if="!data.recent.length" class="muted">
          还没有演绎记录，去探索一个故事吧。
        </p>
      </section>
      <p class="library-footnote">
        以上为平台保存的活动计数，不代表法律能力评分。剩余可用演绎次数：{{
          data.user?.remaining_plays
        }}。
      </p></template
    >
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { api, account } from "../lib/api";
const data = ref(null),
  error = ref("");
onMounted(async () => {
  try {
    data.value = await api("/dashboard");
  } catch (e) {
    error.value = e.message;
  }
});
</script>
