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

  // 设置 Element Plus 语言
  if (locale === "zh-CN") {
    import("element-plus/dist/locale/zh-cn.mjs").then((module) => {
      i18n.global.setLocaleMessage("zh-CN", {
        ...i18n.global.getLocaleMessage("zh-CN"),
        el: module.default,
      });
    });
  } else {
    import("element-plus/dist/locale/en.mjs").then((module) => {
      i18n.global.setLocaleMessage("en-US", {
        ...i18n.global.getLocaleMessage("en-US"),
        el: module.default,
      });
    });
  }
}

export default i18n;
