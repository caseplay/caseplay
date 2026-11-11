import { createRouter, createWebHistory } from "vue-router";
import { account, loadAccount } from "../lib/api";
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      component: () => import("../views/Home.vue"),
      alias: "/home",
      name: "Home",
    },
    {
      path: "/login",
      component: () => import("../views/Login.vue"),
      name: "Login",
      meta: { public: true },
    },
    {
      path: "/register",
      component: () => import("../views/Login.vue"),
      name: "Register",
      meta: { public: true },
    },
    {
      path: "/script/:id",
      component: () => import("../views/ScriptDetail.vue"),
      name: "ScriptDetail",
    },
    {
      path: "/play/:session_id",
      component: () => import("../views/Gameplay.vue"),
      name: "Gameplay",
    },
    {
      path: "/report/:session_id",
      component: () => import("../views/Report.vue"),
      name: "Report",
    },
    {
      path: "/profile",
      component: () => import("../views/Profile.vue"),
      name: "Profile",
    },
    {
      path: "/history",
      component: () => import("../views/History.vue"),
      name: "History",
    },
    {
      path: "/admin",
      component: () => import("../views/Admin.vue"),
      name: "Admin",
    },
  ],
});
router.beforeEach(async (to) => {
  if (to.meta.public) return true;
  if (!account.token) return "/login";
  try {
    await loadAccount();
    if (to.name === "Admin" && !account.user?.is_admin) return "/";
  } catch (_) {
    return "/login";
  }
  return true;
});
export default router;
