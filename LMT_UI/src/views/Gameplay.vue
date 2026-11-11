<template>
  <div class="page play-page" v-if="session">
    <header class="play-heading">
      <div>
        <RouterLink to="/history" class="back-link"
          ><ArrowLeft />我的演绎</RouterLink
        >
        <h1>{{ session.script_title }}</h1>
        <div class="play-meta">
          <span>当前角色：{{ session.character_name }}</span
          ><span>已完成 {{ session.metrics.turns }} 轮行动</span
          ><span class="save-state">自动保存</span>
        </div>
      </div>
      <button
        v-if="session.status === 'ongoing'"
        class="secondary-button"
        @click="finishOpen = true"
        :disabled="busy"
      >
        结束并复盘</button
      ><RouterLink v-else class="primary-button" :to="'/report/' + session.id"
        >查看学习报告<ArrowRight
      /></RouterLink>
    </header>
    <div class="play-layout">
      <section class="play-main">
        <StoryStage
          :roles="session.script.roles"
          :dialogues="currentScene.npc_dialogues || []"
          :narrator="currentScene.narrator_text"
          :scene-type="session.script.scene || 'school'"
          @select-role="target = $event"
        />
        <div class="dialogue-journal">
          <div class="journal-heading">
            <h3><ChatDotRound />剧情与对话</h3>
            <button @click="showHistory = !showHistory">
              {{ showHistory ? "只看当前幕" : "查看完整对话" }}
            </button>
          </div>
          <div class="journal-body" ref="journal">
            <article
              v-for="(item, i) in displayedHistory"
              :key="i"
              :class="['conversation-entry', item.role]"
            >
              <template v-if="item.role === 'user'"
                ><span class="entry-label"
                  >我的行动
                  <small v-if="item.target">对 {{ item.target }}</small></span
                >
                <p>{{ item.content }}</p>
                <small v-if="item.evidence_ids?.length"
                  >已呈递 {{ item.evidence_ids.length }} 条线索</small
                ></template
              ><template v-else
                ><span class="entry-label">情境旁白</span>
                <p class="narration">{{ item.content.narrator_text }}</p>
                <div
                  v-for="(npc, j) in item.content.npc_dialogues"
                  :key="j"
                  class="npc-line"
                >
                  <b>{{ npc.name }}</b
                  ><span>{{ npc.text }}</span>
                </div></template
              >
            </article>
            <div v-if="busy" class="thinking">
              <span></span>AI 角色正在思考你的行动…
            </div>
          </div>
        </div>
        <section v-if="session.status === 'ongoing'" class="action-panel">
          <h3>下一步，你会怎么做？</h3>
          <div class="choice-grid">
            <button
              v-for="choice in currentScene.choices || []"
              :key="choice"
              :disabled="busy"
              @click="act(choice, 'choice')"
            >
              {{ choice }}<ArrowRight />
            </button>
          </div>
          <form @submit.prevent="act(manual, 'custom')">
            <label class="target-select"
              >对话对象<select v-model="target" aria-label="选择对话对象">
                <option value="">由主持人安排</option>
                <option
                  v-for="role in session.script.roles.filter(
                    (r) => r.name !== session.character_name,
                  )"
                  :key="role.name"
                >
                  {{ role.name }}
                </option>
              </select></label
            ><textarea
              v-model="manual"
              placeholder="输入你的提问、判断或行动，可同时呈递右侧已解锁的线索…"
              maxlength="1500"
              :disabled="busy"
              rows="2"
              aria-label="自定义行动"
            ></textarea>
            <div class="action-footer">
              <span>{{
                evidenceIds.length
                  ? `本轮将呈递 ${evidenceIds.length} 条线索`
                  : "有依据的提问，会让推理更进一步。"
              }}</span
              ><button
                class="primary-button"
                :disabled="busy || !manual.trim()"
              >
                发送行动<Promotion />
              </button>
            </div>
          </form>
        </section>
        <div v-else class="completion-panel">
          <CircleCheckFilled />
          <div>
            <h3>故事暂告一段落，思考仍在继续。</h3>
            <p>你的选择、证据与判断路径已保存，前往报告复盘本次经历。</p>
          </div>
          <RouterLink :to="'/report/' + session.id" class="primary-button"
            >打开学习报告<ArrowRight
          /></RouterLink>
        </div>
        <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
      </section>
      <aside class="evidence-panel">
        <div class="evidence-heading">
          <div>
            <span class="eyebrow">CASE NOTES</span>
            <h3>证据与线索板</h3>
          </div>
          <span
            >{{ session.evidence.length }}/{{
              session.script.evidence_count || 4
            }}</span
          >
        </div>
        <p class="muted small">选择已解锁的线索，可随下一次行动呈递给角色。</p>
        <label
          v-for="evidence in session.evidence"
          :key="evidence.id"
          class="evidence-card"
          :class="{
            selected: evidenceIds.includes(evidence.id),
            used: session.evidence_used.includes(evidence.id),
          }"
          ><input
            type="checkbox"
            v-model="evidenceIds"
            :value="evidence.id"
            :disabled="busy || session.status !== 'ongoing'"
          />
          <div>
            <span class="evidence-type"
              ><Document />线索 {{ evidence.id.toUpperCase()
              }}<i v-if="session.evidence_used.includes(evidence.id)"
                >已使用</i
              ></span
            >
            <h4>{{ evidence.title }}</h4>
            <p>{{ evidence.content }}</p>
          </div></label
        >
        <div
          class="locked-evidence"
          v-if="session.evidence.length < (session.script.evidence_count || 4)"
        >
          <Lock />更多线索会随推理推进解锁
        </div>
        <h4 class="evidence-subheading">本次学习目标</h4>
        <ul class="mini-goals">
          <li v-for="goal in session.script.goals" :key="goal">{{ goal }}</li>
        </ul>
      </aside>
    </div>
    <div
      v-if="finishOpen"
      class="modal-backdrop"
      @click.self="finishOpen = false"
    >
      <section class="modal-panel">
        <span class="eyebrow">TIME TO REFLECT</span>
        <h2>准备结束本次演绎？</h2>
        <p>
          系统将结合已经发生的对话与行动生成结局和法理反馈。你也可以继续收集线索。
        </p>
        <div class="modal-actions">
          <button class="secondary-button" @click="finishOpen = false">
            继续探索</button
          ><button class="primary-button" :disabled="busy" @click="finish">
            结束并生成报告
          </button>
        </div>
      </section>
    </div>
  </div>
  <div v-else class="page loading-state">
    {{ error || "正在恢复你的故事…" }}
  </div>
</template>
<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import {
  ArrowLeft,
  ArrowRight,
  ChatDotRound,
  Promotion,
  Document,
  Lock,
  CircleCheckFilled,
} from "@element-plus/icons-vue";
import StoryStage from "../components/StoryStage.vue";
import { api } from "../lib/api";
const route = useRoute(),
  session = ref(null),
  busy = ref(false),
  error = ref(""),
  manual = ref(""),
  target = ref(""),
  evidenceIds = ref([]),
  showHistory = ref(false),
  finishOpen = ref(false),
  journal = ref(null);
const currentScene = computed(
  () =>
    [...(session.value?.chat_history || [])]
      .reverse()
      .find((x) => x.role === "ai")?.content || {},
);
const displayedHistory = computed(() =>
  showHistory.value
    ? session.value.chat_history
    : session.value.chat_history
        .slice(-2)
        .filter((x, i, arr) => arr.length === 1 || x.role === "ai" || i === 0),
);
onMounted(async () => {
  try {
    session.value = await api("/sessions/" + route.params.session_id);
  } catch (e) {
    error.value = e.message;
  }
});
async function act(action, mode = "custom", end = false) {
  if (busy.value || !action.trim()) return;
  busy.value = true;
  error.value = "";
  try {
    const result = await api("/play/action", {
      method: "POST",
      body: {
        session_id: session.value.id,
        action,
        mode,
        evidence_ids: evidenceIds.value,
        target: target.value,
        finish: end,
      },
    });
    session.value = result.session;
    manual.value = "";
    evidenceIds.value = [];
    await nextTick();
    if (journal.value) journal.value.scrollTop = journal.value.scrollHeight;
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
async function finish() {
  finishOpen.value = false;
  await act(
    "我已完成本轮事实梳理和求助安排，现在结束演绎。请结合我的实际行动总结结局，并生成法理反馈和学习建议。",
    "custom",
    true,
  );
}
</script>
