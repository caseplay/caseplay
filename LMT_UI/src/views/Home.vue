<template>
  <div class="page library-page">
    <header class="page-top">
      <div>
        <span class="eyebrow">THE STORY STARTS HERE</span>
        <h1>
          你好，{{ account.user?.display_name }}<span class="teal-dot">。</span>
        </h1>
        <p class="muted">走进一个故事，换个角色理解世界。</p>
      </div>
      <div class="date-label"><Calendar />今日宜探索，宜思考</div>
    </header>
    <section class="library-hero">
      <div>
        <span class="hero-kicker">让知识发生在你的选择里</span>
        <h2>不只是阅读案例，<br />更是参与其中。</h2>
        <p>
          与 AI 角色对话，整理线索与证据，<br />在真实的思考过程中，建立自己的规则意识。
        </p>
        <button
          class="light-button"
          @click="featured && $router.push('/script/' + featured.id)"
        >
          开启一场演绎<ArrowRight />
        </button>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="hero-orbit one"></div>
        <div class="hero-orbit two"></div>
        <div class="hero-document">
          <span>CASE FILE</span>
          <h3>让事实<br />与证据说话</h3>
          <i></i><i></i><i></i>
          <div class="seal-outline"><ScaleToOriginal /></div>
        </div>
        <div class="hero-chip"><ChatDotRound />一次选择，多种视角</div>
      </div>
    </section>
    <section
      v-if="dashboard?.recent?.some((s) => s.status === 'ongoing')"
      class="resume-banner"
    >
      <div>
        <span class="tiny-dot"></span><b>还有一个故事，等你继续</b
        ><span>{{ ongoing.script_title }}</span>
      </div>
      <RouterLink :to="'/play/' + ongoing.id"
        >继续演绎<ArrowRight
      /></RouterLink>
    </section>
    <div class="section-heading">
      <div>
        <span class="eyebrow">EXPLORE THE CASES</span>
        <h2>选择你的下一段故事</h2>
      </div>
      <span class="count-label">{{ items.length }} 个教学剧本</span>
    </div>
    <div class="library-filters">
      <div class="category-tabs">
        <button
          v-for="c in categories"
          :key="c"
          :class="{ active: category === c }"
          @click="category = c"
        >
          {{ c }}
        </button>
      </div>
      <div class="filter-tools">
        <label class="search-box"
          ><Search /><input
            v-model="query"
            placeholder="搜索主题、剧本或法律问题"
            aria-label="搜索剧本" /></label
        ><select v-model="difficulty" aria-label="筛选难度">
          <option value="">全部难度</option>
          <option>入门</option>
          <option>进阶</option>
          <option>挑战</option></select
        ><button
          class="favorite-filter"
          :class="{ active: favoritesOnly }"
          @click="favoritesOnly = !favoritesOnly"
        >
          <Star />{{ favoritesOnly ? "已收藏" : "我的收藏" }}
        </button>
      </div>
    </div>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <div v-if="busy" class="loading-state">正在整理剧本…</div>
    <div v-else class="script-grid">
      <article
        v-for="(script, i) in items"
        :key="script.id"
        class="script-card"
        :class="script.accent"
      >
        <RouterLink :to="'/script/' + script.id" class="script-art"
          ><span class="case-number"
            >CASE {{ String(i + 1).padStart(2, "0") }}</span
          ><component :is="icon(script)" />
          <div class="art-circle"></div>
          <span class="art-category">{{ script.category }}</span></RouterLink
        >
        <div class="script-copy">
          <div class="script-meta">
            <span>{{ script.difficulty }}</span
            ><span>{{ script.duration }} 分钟</span
            ><button
              class="star-button"
              :class="{ saved: script.favorite }"
              :aria-label="
                script.favorite
                  ? '取消收藏 ' + script.title
                  : '收藏 ' + script.title
              "
              @click="toggleFavorite(script)"
            >
              <StarFilled v-if="script.favorite" /><Star v-else />
            </button>
          </div>
          <RouterLink :to="'/script/' + script.id"
            ><h3>{{ script.title }}</h3></RouterLink
          >
          <p class="script-subtitle">{{ script.subtitle }}</p>
          <p class="script-summary">{{ script.summary }}</p>
          <div class="script-bottom">
            <span
              >{{ script.roles.length }} 个角色<span class="middle-dot">·</span
              >{{ script.evidence_count }} 条线索</span
            ><RouterLink
              :to="'/script/' + script.id"
              :aria-label="'探索 ' + script.title"
              ><ArrowRight
            /></RouterLink>
          </div>
        </div>
      </article>
    </div>
    <div v-if="!busy && !items.length" class="empty-state">
      <Search />
      <h3>暂时没有找到对应剧本</h3>
      <p>试试更短的关键词，或切换一个主题。</p>
      <button class="secondary-button" @click="reset">重置筛选</button>
    </div>
    <div class="library-footnote">
      所有案例均为教学情境，角色与故事服务于法治学习。参考法规来源可在剧本详情中查看。
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, watch } from "vue";
import {
  Search,
  Star,
  StarFilled,
  ArrowRight,
  Calendar,
  ChatDotRound,
  ScaleToOriginal,
  School,
  Lock,
  House,
  Cpu,
} from "@element-plus/icons-vue";
import { api, account } from "../lib/api";
const items = ref([]),
  dashboard = ref(null),
  busy = ref(true),
  error = ref(""),
  category = ref("全部故事"),
  difficulty = ref(""),
  query = ref(""),
  favoritesOnly = ref(false);
const categories = ["全部故事", "校园保护", "网络安全", "民事生活", "科技社会"];
const featured = computed(() => items.value[0]);
const ongoing = computed(() =>
  dashboard.value?.recent.find((s) => s.status === "ongoing"),
);
function icon(s) {
  return (
    { 校园保护: School, 网络安全: Lock, 民事生活: House, 科技社会: Cpu }[
      s.category
    ] || School
  );
}
let timer,
  generation = 0;
async function load() {
  const ticket = ++generation;
  busy.value = true;
  error.value = "";
  try {
    const params = new URLSearchParams({
      q: query.value,
      ...(category.value !== "全部故事" ? { category: category.value } : {}),
      ...(difficulty.value ? { difficulty: difficulty.value } : {}),
      ...(favoritesOnly.value ? { favorite: "1" } : {}),
    });
    const result = await api("/scripts?" + params);
    if (ticket === generation) items.value = result;
  } catch (e) {
    if (ticket === generation) error.value = e.message;
  } finally {
    if (ticket === generation) busy.value = false;
  }
}
async function toggleFavorite(script) {
  try {
    script.favorite = (
      await api(`/scripts/${script.id}/favorite`, { method: "POST" })
    ).favorite;
    if (favoritesOnly.value) await load();
  } catch (e) {
    error.value = e.message;
  }
}
function reset() {
  category.value = "全部故事";
  query.value = "";
  difficulty.value = "";
  favoritesOnly.value = false;
}
watch([category, difficulty, query, favoritesOnly], () => {
  clearTimeout(timer);
  timer = setTimeout(load, 180);
});
onMounted(async () => {
  await load();
  try {
    dashboard.value = await api("/dashboard");
  } catch (_) {}
});
</script>
