<template>
  <div class="page report-page">
    <header class="page-top">
      <div>
        <span class="eyebrow">REFLECT ON YOUR CHOICES</span>
        <h1>故事之后，留下思考。</h1>
        <p class="muted">
          回看选择背后的理由，把一次经历变成下一次行动的依据。
        </p>
      </div>
      <div class="inline-actions">
        <button class="secondary-button" @click="download">导出对局</button
        ><button class="primary-button" @click="print">打印报告</button>
      </div>
    </header>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <template v-if="data"
      ><section class="report-cover">
        <span class="tag">学习反馈报告</span>
        <h2>{{ data.script_title }}</h2>
        <p>
          扮演角色：{{ data.character_name }} <span class="middle-dot">·</span
          >{{ new Date(data.created_at).toLocaleDateString("zh-CN") }}
        </p>
        <div class="report-stats">
          <div
            v-for="(n, i) in [
              data.metrics.turns,
              data.metrics.evidence_count,
              data.metrics.custom_actions,
            ]"
            :key="i"
          >
            <strong>{{ n }}</strong
            ><span>{{ ["行动轮次", "呈递线索", "自主行动"][i] }}</span>
          </div>
        </div>
      </section>
      <div class="report-columns">
        <section class="panel">
          <span class="eyebrow">STORY & REASONING</span>
          <h2>结局与法理解析</h2>
          <p class="report-text">{{ data.end_report }}</p>
          <p class="report-disclaimer">
            由
            {{
              data.model_label
            }}
            根据本次对话生成，用于教学复盘；具体法律问题请结合事实核实。
          </p>
        </section>
        <aside class="panel">
          <span class="eyebrow">NEXT STEPS</span>
          <h2>你的下一步</h2>
          <ul class="goals">
            <li v-for="p in data.script.learning_points" :key="p">{{ p }}</li>
          </ul>
          <h3>延伸阅读</h3>
          <a
            class="law-link"
            v-for="r in data.script.legal_references"
            :key="r.url"
            :href="r.url"
            target="_blank"
            rel="noopener noreferrer"
            >{{ r.title }} ↗</a
          >
        </aside>
      </div>
      <section class="panel" v-if="data.feedback.length">
        <div class="section-heading">
          <h2>过程观察与建议</h2>
          <span class="muted small">AI 定性反馈 · 无能力打分</span>
        </div>
        <div class="feedback-grid">
          <article v-for="(f, i) in data.feedback" :key="i">
            <span class="feedback-number">0{{ i + 1 }}</span>
            <h3>{{ f.dimension }}</h3>
            <p>{{ f.observation }}</p>
            <div>{{ f.suggestion }}</div>
          </article>
        </div>
      </section>
      <section class="panel reflection-panel">
        <span class="eyebrow">A NOTE TO YOURSELF</span>
        <h2>写下这一次的收获</h2>
        <p class="muted">
          如果再遇到类似的情境，你会如何收集事实、表达观点或寻求帮助？
        </p>
        <textarea
          v-model="reflection"
          rows="4"
          maxlength="4000"
          aria-label="个人复盘"
          placeholder="我学到的是…下一次我会…"
        ></textarea>
        <div class="action-footer">
          <span class="muted" role="status">{{ saved }}</span
          ><button class="primary-button" :disabled="saving" @click="save">
            {{ saving ? "正在保存…" : "保存我的复盘" }}
          </button>
        </div>
      </section>
      <RouterLink to="/" class="back-link"
        >← 探索下一个故事</RouterLink
      ></template
    >
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { api, exportSession } from "../lib/api";
const route = useRoute(),
  data = ref(null),
  reflection = ref(""),
  error = ref(""),
  saved = ref(""),
  saving = ref(false);
const print = () => window.print();
async function download() {
  try {
    await exportSession(data.value.id);
  } catch (e) {
    error.value = e.message;
  }
}
async function save() {
  saving.value = true;
  try {
    await api("/sessions/" + data.value.id + "/reflection", {
      method: "POST",
      body: { reflection: reflection.value },
    });
    saved.value = "已保存到你的学习档案";
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
onMounted(async () => {
  try {
    data.value = await api("/report/" + route.params.session_id);
    reflection.value = data.value.reflection;
  } catch (e) {
    error.value = e.message;
  }
});
</script>
