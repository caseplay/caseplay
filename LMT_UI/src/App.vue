<template>
  <div class="app-shell">
    <aside v-if="!$route.meta.public" class="sidebar">
      <RouterLink to="/" class="brand"
        ><span class="brand-mark">C<span></span></span>
        <div>Caseplay<small>智法剧场</small></div></RouterLink
      >
      <p class="nav-label">沉浸式法治学习</p>
      <RouterLink to="/" class="nav-item" exact-active-class="active"
        ><Compass />剧本探索</RouterLink
      >
      <RouterLink to="/history" class="nav-item" active-class="active"
        ><Clock />我的演绎</RouterLink
      >
      <RouterLink to="/profile" class="nav-item" active-class="active"
        ><DataLine />学习档案</RouterLink
      >
      <RouterLink
        v-if="account.user?.is_admin"
        to="/admin"
        class="nav-item"
        active-class="active"
        ><EditPen />内容工作台</RouterLink
      >
      <div class="sidebar-note">
        <span>PLAY. REASON. REFLECT.</span>
        <p>在故事里作出选择，<br />在复盘中理解规则。</p>
      </div>
      <div class="account">
        <div class="avatar">
          {{ account.user?.display_name?.slice(0, 1) || "学" }}
        </div>
        <div>
          <b>{{ account.user?.display_name || "学习者" }}</b
          ><small>{{
            account.user?.is_admin ? "内容管理员" : "情境探索者"
          }}</small>
        </div>
        <button aria-label="退出登录" @click="logout"><SwitchButton /></button>
      </div>
    </aside>
    <main :class="['workspace', { public: $route.meta.public }]">
      <RouterView :key="$route.fullPath" />
    </main>
  </div>
</template>
<script setup>
import {
  Compass,
  Clock,
  DataLine,
  EditPen,
  SwitchButton,
} from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { account, signOut } from "./lib/api";
const router = useRouter();
async function logout() {
  await signOut();
  router.push("/login");
}
</script>
