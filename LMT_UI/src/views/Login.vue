<template>
  <div class="auth-page">
    <section class="auth-story">
      <RouterLink to="/login" class="brand light"
        ><span class="brand-mark">C<span></span></span>
        <div>Caseplay<small>智法剧场</small></div></RouterLink
      >
      <div class="auth-copy">
        <div class="eyebrow">YOUR CHOICES MATTER</div>
        <h1>每一个选择，<br />都值得被理解。</h1>
        <p>
          走进不同的角色，寻找事实与证据。<br />让法治学习发生在你参与的故事里。
        </p>
        <div class="auth-scene">
          <div class="paper one"><span>事实</span><i></i><i></i><i></i></div>
          <div class="paper two"><span>证据</span><i></i><i></i><i></i></div>
          <div class="auth-orbit"></div>
          <div class="scale-symbol">⚖</div>
        </div>
      </div>
      <small class="auth-credit">情境推理 / 角色互动 / 法理复盘</small>
    </section>
    <section class="auth-form">
      <div class="auth-form-inner">
        <span class="eyebrow">START YOUR STORY</span>
        <h2>{{ register ? "创建你的学习账号" : "欢迎回到智法剧场" }}</h2>
        <p class="muted">
          {{
            register
              ? "从一个真实的选择开始，开启你的法治探索。"
              : "你的故事与思考，已经为你妥善保存。"
          }}
        </p>
        <form @submit.prevent="submit">
          <label v-if="register"
            >学习昵称<input
              v-model="form.display_name"
              placeholder="例如：小林同学"
              minlength="2"
              maxlength="40"
              required
              autocomplete="nickname"
          /></label>
          <label
            >邮箱地址<input
              v-model="form.email"
              type="email"
              placeholder="yourname@example.com"
              autocomplete="email"
              required
          /></label>
          <label
            >登录密码
            <div class="password-field">
              <input
                v-model="form.password"
                :type="show ? 'text' : 'password'"
                :autocomplete="register ? 'new-password' : 'current-password'"
                placeholder="至少8位字符"
                minlength="8"
                maxlength="128"
                required
              /><button
                type="button"
                @click="show = !show"
                :aria-label="show ? '隐藏密码' : '显示密码'"
              >
                {{ show ? "隐藏" : "显示" }}
              </button>
            </div></label
          >
          <label v-if="register" class="check-label"
            ><input
              v-model="form.accepted_terms"
              type="checkbox"
              required
            /><span
              >我了解这是教学情境平台，同意保存本账号的演绎与学习记录。</span
            ></label
          >
          <p v-if="error" class="error-banner" role="alert">{{ error }}</p>
          <button class="primary-button auth-submit" :disabled="busy">
            {{
              busy
                ? "正在进入…"
                : register
                  ? "注册并开启探索"
                  : "登录并继续探索"
            }}<ArrowRight />
          </button>
        </form>
        <p class="auth-switch">
          {{ register ? "已有账号？" : "第一次来到这里？" }}
          <RouterLink :to="register ? '/login' : '/register'">{{
            register ? "直接登录" : "创建账号"
          }}</RouterLink>
        </p>
        <div class="auth-bottom">
          <Lock />密码加密存储，演绎记录仅你本人可见。
        </div>
      </div>
    </section>
  </div>
</template>
<script setup>
import { reactive, computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowRight, Lock } from "@element-plus/icons-vue";
import { api, saveAccount } from "../lib/api";
const route = useRoute(),
  router = useRouter(),
  register = computed(() => route.name === "Register"),
  show = ref(false),
  busy = ref(false),
  error = ref("");
const form = reactive({
  display_name: "",
  email: "",
  password: "",
  accepted_terms: false,
});
async function submit() {
  busy.value = true;
  error.value = "";
  try {
    saveAccount(
      await api(register.value ? "/auth/register" : "/auth/login", {
        method: "POST",
        body: form,
      }),
    );
    router.push("/");
  } catch (e) {
    error.value = e.message;
  } finally {
    busy.value = false;
  }
}
</script>
