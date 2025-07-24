import { createRouter, createWebHistory } from "vue-router";
import Login from "../views/Login.vue";
import Register from "../views/Register.vue";
import Home from "../views/Home.vue";
import Dashboard from "../views/Dashboard.vue";
import Clients from "../views/Clients.vue";
import Nodes from "../views/Nodes.vue";
import Storages from "../views/Storages.vue";
import Tasks from "../views/Tasks.vue";
import Logs from "../views/Logs.vue";
import Settings from "../views/Settings.vue";
import NotFound from "../views/NotFound.vue";
import Profile from "../views/Profile.vue";
import AuditLogs from "../views/AuditLogs.vue";
import VerifyEmail from "../views/VerifyEmail.vue";
import RegisterMailSent from "../views/RegisterMailSent.vue";
import ForgotPassword from "../views/ForgotPassword.vue";
import ResetPassword from "../views/ResetPassword.vue";
import ResetMailSent from "../views/ResetMailSent.vue";

const routes = [
  {
    path: "/",
    redirect: "/dashboard",
  },
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { requiresAuth: false },
  },
  {
    path: "/register_mail_sent",
    name: "RegisterMailSent",
    component: RegisterMailSent,
    meta: { requiresAuth: false },
  },
  {
    path: "/verify_email",
    name: "VerifyEmail",
    component: VerifyEmail,
    meta: { requiresAuth: false },
  },
  {
    path: "/forgot_password",
    name: "ForgotPassword",
    component: ForgotPassword,
    meta: { requiresAuth: false },
  },
  {
    path: "/reset_password",
    name: "ResetPassword",
    component: ResetPassword,
    meta: { requiresAuth: false },
  },
  {
    path: "/reset_mail_sent",
    name: "ResetMailSent",
    component: ResetMailSent,
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    name: "Home",
    component: Home,
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: Dashboard,
      },
      {
        path: "clients",
        name: "Clients",
        component: Clients,
      },
      {
        path: "nodes",
        name: "Nodes",
        component: Nodes,
      },
      {
        path: "storages",
        name: "Storages",
        component: Storages,
      },
      {
        path: "tasks",
        name: "Tasks",
        component: Tasks,
      },
      {
        path: "logs",
        name: "Logs",
        component: Logs,
      },
      {
        path: "settings",
        name: "Settings",
        component: Settings,
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: "profile",
        name: "Profile",
        component: Profile,
      },
      {
        path: "audit-logs",
        name: "AuditLogs",
        component: AuditLogs,
        meta: { requiresAuth: true, requiresAdmin: true },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: NotFound,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const access_token = localStorage.getItem("access_token");

  // 如果访问需要认证的页面但没有token
  if (to.meta.requiresAuth && !access_token) {
    next("/login");
    return;
  }

  // 如果已登录用户访问登录或注册页面
  if ((to.name === "Login" || to.name === "Register") && access_token) {
    next("/dashboard");
    return;
  }

  next();
});

export default router;
