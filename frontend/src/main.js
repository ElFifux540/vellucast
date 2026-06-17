import { createApp } from "vue";
import App from "./App.vue";
import "./assets/main.css";
import { initTheme } from "./theme.js";

initTheme();
createApp(App).mount("#app");
