import { createI18n } from "vue-i18n";
import zhCN from "./locales/zh-CN";
import enUS from "./locales/en-US";

// 获取浏览器语言设置
function getDefaultLocale() {
  const savedLocale = localStorage.getItem("locale");
  if (savedLocale) {
    return savedLocale;
  }

  const browserLocale = navigator.language || navigator.userLanguage;
  if (browserLocale.startsWith("zh")) {
    return "zh-CN";
  }
  return "en-US";
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API
  locale: getDefaultLocale(),
  fallbackLocale: "zh-CN",
  messages: {
    "zh-CN": zhCN,
    "en-US": enUS,
  },
  globalInjection: true, // 全局注入 $t 函数
  silentTranslationWarn: process.env.NODE_ENV === "production",
});

// 语言切换函数
export function setLocale(locale) {
  i18n.global.locale.value = locale;
  localStorage.setItem("locale", locale);

  // 设置 HTML lang 属性
  document.documentElement.lang = locale;

  // 更新Element Plus的locale
  if (locale === "zh-CN") {
    import("element-plus/dist/locale/zh-cn.mjs").then((module) => {
      // 更新全局配置
      if (window.$ELEMENT) {
        window.$ELEMENT.locale = module.default;
      }
      // 更新app实例的全局配置
      const app = document.querySelector("#app").__vue_app__;
      if (app && app.config.globalProperties.$ELEMENT) {
        app.config.globalProperties.$ELEMENT.locale = module.default;
      }
    });
  } else {
    import("element-plus/dist/locale/en.mjs").then((module) => {
      // 更新全局配置
      if (window.$ELEMENT) {
        window.$ELEMENT.locale = module.default;
      }
      // 更新app实例的全局配置
      const app = document.querySelector("#app").__vue_app__;
      if (app && app.config.globalProperties.$ELEMENT) {
        app.config.globalProperties.$ELEMENT.locale = module.default;
      }
    });
  }
}

export default i18n;
