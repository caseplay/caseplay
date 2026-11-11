<template>
  <div class="page detail-page" v-if="script">
    <RouterLink to="/" class="back-link"><ArrowLeft />返回剧本探索</RouterLink>
    <header class="detail-hero" :class="script.accent">
      <div class="detail-hero-copy">
        <span class="eyebrow"
          >{{ script.category }} / {{ script.difficulty }}</span
        >
        <h1>{{ script.title }}</h1>
        <p>{{ script.summary }}</p>
        <div class="detail-pills">
          <span><Clock />{{ script.duration }} 分钟</span
          ><span><User />{{ script.roles.length }} 个角色</span
          ><span><Document />{{ script.evidence_count }} 条线索</span>
        </div>
      </div>
      <div class="detail-hero-art">
        <Reading /><span>EVERY PERSPECTIVE COUNTS</span>
      </div>
    </header>
    <div class="detail-columns">
      <section>
        <div class="section-heading">
          <div>
            <span class="eyebrow">CHOOSE YOUR PERSPECTIVE</span>
            <h2>你想从谁的视角出发？</h2>
          </div>
        </div>
        <div class="role-grid">
          <button
            v-for="(role, i) in script.roles"
            :key="role.name"
            class="role-card"
            :class="{ selected: character === role.name }"
            @click="character = role.name"
          >
            <span class="role-avatar" :class="'tone-' + (i % 4)"
              ><UserFilled
            /></span>
            <h3>{{ role.name }}</h3>
            <p>{{ role.description }}</p>
            <span class="role-check">{{
              character === role.name ? "已选择 ✓" : "选择这个角色"
            }}</span>
          </button>
        </div>
        <div class="case-context">
          <h3>案件序章</h3>
          <p>{{ script.context }}</p>
        </div>
      </section>
      <aside class="detail-aside">
        <h3>这段故事，你将探索</h3>
        <ol class="goal-list">
          <li v-for="goal in script.goals" :key="goal">{{ goal }}</li>
        </ol>
        <div class="aside-rule"></div>
        <h4>官方法规阅读</h4>
        <a
          v-for="reference in script.legal_references"
          :key="reference.url"
          :href="reference.url"
          target="_blank"
          rel="noopener noreferrer"
          class="law-link"
          ><Document />{{ reference.title }}<TopRight
        /></a>
        <p class="small muted">
          这是教学情境。请在推演中区分事实、推测与适用条件。
        </p>
        <button
          class="primary-button"
          @click="start"
          :disabled="!character || busy"
        >
          {{ busy ? "AI 正在布置第一幕…" : "进入三维剧场" }}<ArrowRight />
        </button>
        <p v-if="error" class="error-banner">{{ error }}</p>
      </aside>
    </div>
  </div>
  <div v-else class="page loading-state">
    {{ error || "正在打开案例档案…" }}
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowLeft,
  ArrowRight,
  Clock,
  User,
  UserFilled,
  Document,
  Reading,
  TopRight,
} from "@element-plus/icons-vue";
import { api } from "../lib/api";
const route = useRoute(),
  router = useRouter(),
  script = ref(null),
  character = ref(""),
  busy = ref(false),
  error = ref("");
onMounted(async () => {
  try {
    script.value = await api("/scripts/" + route.params.id);
  } catch (e) {
    error.value = e.message;
  }
});
async function start() {
  busy.value = true;
  error.value = "";
  try {
    const result = await api("/play/start", {
      method: "POST",
      body: { script_id: script.value.id, character: character.value },
    });
    router.push("/play/" + result.session_id);
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
