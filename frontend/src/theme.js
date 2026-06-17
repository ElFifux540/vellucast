/**
 * Gestion du thème clair / sombre / auto (suit le thème du système).
 * Le mode choisi est persisté par navigateur (localStorage).
 */
const STORAGE_KEY = "vellucast_theme";
const media = () => window.matchMedia("(prefers-color-scheme: dark)");

export function getTheme() {
  try {
    return localStorage.getItem(STORAGE_KEY) || "auto";
  } catch (e) {
    return "auto";
  }
}

export function applyTheme(mode) {
  const dark = mode === "dark" || (mode === "auto" && media().matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function setTheme(mode) {
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch (e) {
    /* no-op */
  }
  applyTheme(mode);
  window.dispatchEvent(new Event("vellucast-theme"));
}

export function initTheme() {
  applyTheme(getTheme());
  // Suit les changements du thème système quand le mode est « auto ».
  media().addEventListener("change", () => {
    if (getTheme() === "auto") applyTheme("auto");
  });
}
