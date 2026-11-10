<template>
  <div class="login-page">
    <div class="glass-panel login-box">
      <h2>{{ isLogin ? '登录' : '注册账号' }}</h2>
      <p class="subtitle">{{ isLogin ? '欢迎回到 Caseplay' : '创建一个账号开启普法之旅' }}</p>

      <form @submit.prevent="handleSubmit">
        <div class="input-group">
          <input type="email" v-model="form.email" placeholder="邮箱地址" required />
        </div>

        <div class="input-group code-group" v-if="!isLogin">
          <input type="text" v-model="form.code" placeholder="验证码" required />
          <button type="button" @click="sendCode" :disabled="!form.email || countdown > 0">
            {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
          </button>
        </div>

        <div class="input-group">
          <input type="password" v-model="form.password" placeholder="密码" required />
        </div>

        <button type="submit" class="submit-btn">{{ isLogin ? '登录并进入' : '注册' }}</button>
      </form>

      <p class="toggle-mode">
        {{ isLogin ? "还没有账号？" : "已经有账号？" }}
        <a href="#" @click.prevent="isLogin = !isLogin">{{ isLogin ? '注册账号' : '直接登录' }}</a>
      </p>

      <p class="error-msg" v-if="errorMsg">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const isLogin = ref(true)
const countdown = ref(0)
const errorMsg = ref('')

const form = reactive({
  email: '',
  code: '',
  password: ''
})

const API_BASE = `${import.meta.env.VITE_API_BASE || '/api'}/auth`

const startCountdown = () => {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

const sendCode = async () => {
  errorMsg.value = ''

  // Regex check for email
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.email)) {
    errorMsg.value = '邮箱格式不正确'
    ElMessage.error(errorMsg.value)
    return
  }

  try {
    const res = await axios.post(`${API_BASE}/send_code`, { email: form.email })

    if (res.data.user_exists && !isLogin.value) {
      ElMessageBox.alert('此邮箱已经注册过。再次注册即代表修改您的密码！', '提示', {
        confirmButtonText: '明白',
        type: 'warning',
      })
    } else {
      ElMessage.success('验证码已发送！')
    }

    startCountdown()
  } catch (err) {
    errorMsg.value = err.response?.data?.error || '验证码发送失败，请重试。'
    ElMessage.error(errorMsg.value)
  }
}

const handleSubmit = async () => {
  errorMsg.value = ''
  try {
    if (isLogin.value) {
      const res = await axios.post(`${API_BASE}/login`, {
        email: form.email,
        password: form.password
      })
      localStorage.setItem('token', res.data.token)
      ElMessage.success('登录成功！')
      router.push({ name: 'Home' })
    } else {
      const resp = await axios.post(`${API_BASE}/register`, form)
      isLogin.value = true
      form.code = ''
      if (resp.data.is_update) {
        ElMessage.success('密码修改成功！请重新登录。')
      } else {
        ElMessage.success('注册成功！请登录。')
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.error || '操作发生错误，请重试。'
    ElMessage.error(errorMsg.value)
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 65px);
  padding: 2rem;
}
.login-box {
  width: 100%;
  max-width: 400px;
  text-align: center;
}
h2 {
  margin-bottom: 0.5rem;
  font-size: 2rem;
}
.subtitle {
  color: var(--text-muted);
  margin-bottom: 2rem;
}
.code-group {
  display: flex;
  gap: 1rem;
}
.code-group input {
  flex: 1;
}
.code-group button {
  white-space: nowrap;
  margin-bottom: 1rem;
}
.submit-btn {
  width: 100%;
  margin-top: 1rem;
  padding: 0.8rem;
  font-size: 1.1rem;
}
.toggle-mode {
  margin-top: 1.5rem;
  color: var(--text-muted);
}
.toggle-mode a {
  color: var(--primary);
  text-decoration: none;
}
.error-msg {
  color: #ef4444;
  margin-top: 1rem;
  font-size: 0.9rem;
}
</style>
