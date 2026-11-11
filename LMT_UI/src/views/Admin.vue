<template>
  <div class="page">
    <header class="page-top">
      <div>
        <span class="eyebrow">CONTENT STUDIO</span>
        <h1>内容工作台</h1>
        <p class="muted">AI 起草、人工审校，让教学情境有据可依。</p>
      </div>
    </header>
    <p v-if="error" class="error-banner">{{ error }}</p>
    <section class="panel">
      <h2>创建新的教学剧本</h2>
      <form @submit.prevent="generate">
        <div class="filter-tools">
          <select v-model="category" aria-label="草稿分类">
            <option v-for="c in categories" :key="c">{{ c }}</option></select
          ><input
            v-model="topic"
            placeholder="输入教学主题、冲突与学习目标（至少4字）"
            minlength="4"
            maxlength="300"
            required
          /><button class="primary-button" :disabled="busy">
            {{ busy ? "正在起草…" : "AI 生成草稿" }}
          </button>
        </div>
      </form>
      <p class="muted small">
        生成内容默认不进入剧本库，需人工核对事实、法理、角色与线索后发布。
      </p>
    </section>
    <div class="admin-layout">
      <section class="panel">
        <h2>草稿与发布记录</h2>
        <button
          class="draft-item"
          v-for="d in drafts"
          :key="d.id"
          @click="choose(d)"
        >
          <b>{{ d.payload.title }}</b
          ><span class="tag">{{
            d.status === "published" ? "已审校发布" : "待审校"
          }}</span>
        </button>
        <p class="muted" v-if="!drafts.length">尚无草稿，先创建一个主题。</p>
      </section>
      <section class="panel" v-if="selected">
        <h2>{{ selected.payload.title }}</h2>
        <p class="muted small">
          可编辑结构化内容，包含角色、证据解锁顺序与官方法规链接。
        </p>
        <textarea
          v-model="editor"
          rows="18"
          aria-label="剧本草稿内容"
          :disabled="selected.status === 'published'"
          spellcheck="false"
        ></textarea
        ><template v-if="selected.status !== 'published'"
          ><button class="secondary-button" @click="saveDraft" :disabled="busy">
            保存草稿修改</button
          ><label class="field-label"
            >人工审校意见<textarea
              v-model="note"
              rows="3"
              minlength="8"
              placeholder="记录法理核验、线索一致性与教学适用性检查（至少8字）"
            ></textarea></label
          ><button
            class="primary-button"
            @click="publish"
            :disabled="busy || note.trim().length < 8"
          >
            确认审校并发布到剧本库
          </button></template
        >
        <p v-else class="success-banner">{{ selected.review_note }}</p>
      </section>
    </div>
    <section class="panel">
      <h2>学习者使用额度</h2>
      <div class="user-row" v-for="u in users" :key="u.id">
        <span
          >{{ u.display_name }}<small>{{ u.email }}</small></span
        ><label
          >剩余次数
          <input
            type="number"
            v-model.number="u.remaining_plays"
            min="0"
            max="10000" /></label
        ><button class="secondary-button" @click="saveUser(u)">保存额度</button>
      </div>
    </section>
    <p class="success-banner" v-if="message" role="status">{{ message }}</p>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { api } from "../lib/api";
const categories = ["校园保护", "网络安全", "民事生活", "科技社会"],
  category = ref("校园保护"),
  topic = ref(""),
  drafts = ref([]),
  users = ref([]),
  selected = ref(null),
  editor = ref(""),
  note = ref(""),
  busy = ref(false),
  error = ref(""),
  message = ref("");
async function load() {
  [drafts.value, users.value] = await Promise.all([
    api("/admin/drafts"),
    api("/admin/users"),
  ]);
}
function choose(d) {
  selected.value = d;
  editor.value = JSON.stringify(d.payload, null, 2);
  note.value = d.review_note || "";
}
async function perform(fn) {
  busy.value = true;
  error.value = "";
  message.value = "";
  try {
    await fn();
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function generate() {
  await perform(async () => {
    const d = await api("/admin/drafts/generate", {
      method: "POST",
      body: { topic: topic.value, category: category.value },
    });
    await load();
    choose(d);
  });
}
async function saveDraft() {
  await perform(async () => {
    const d = await api("/admin/drafts/" + selected.value.id, {
      method: "PUT",
      body: { payload: JSON.parse(editor.value) },
    });
    await load();
    choose(d);
    message.value = "草稿已保存";
  });
}
async function publish() {
  await perform(async () => {
    await api("/admin/drafts/" + selected.value.id, {
      method: "PUT",
      body: { payload: JSON.parse(editor.value) },
    });
    const d = await api("/admin/drafts/" + selected.value.id + "/publish", {
      method: "POST",
      body: { review_note: note.value },
    });
    await load();
    choose(d);
    message.value = "剧本已发布";
  });
}
async function saveUser(u) {
  await perform(async () => {
    await api("/admin/users/" + u.id, {
      method: "PUT",
      body: { remaining_plays: u.remaining_plays },
    });
    message.value = "额度已更新";
  });
}
onMounted(() => perform(load));
</script>
