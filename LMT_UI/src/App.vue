<template>
  <div class="app-container">
    <nav v-if="$route.name !== 'Login'" class="navbar">
      <div class="logo" @click="router.push('/')" style="cursor: pointer;">⚖️ Caseplay</div>
      <div class="nav-actions" v-if="isLoggedIn">
        <button class="nav-btn" @click="router.push('/profile')">个人主页</button>
        <button class="nav-btn logout-btn" @click="logout">退出登录</button>
      </div>
    </nav>
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

const logout = () => {
  localStorage.removeItem('token')
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.main-content {
  flex: 1;
  position: relative;
}
.nav-actions {
  display: flex;
  gap: 1rem;
}
.nav-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-main);
}
.nav-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}
.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border-color: #ef4444;
}
</style>
