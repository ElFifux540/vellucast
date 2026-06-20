/**
 * Gestion du thème (clair / sombre / auto) et de la palette d'accent.
 * Tout est persisté par navigateur (localStorage). « auto » suit le système.
 */
const THEME_KEY = "vellucast_theme";
const ACCENT_KEY = "vellucast_accent";
const ACCENTS = ["indigo", "violet", "emerald", "ocean", "rose", "amber"];
const media = () => window.matchMedia("(prefers-color-scheme: dark)");

export function getTheme() {
  try { return localStorage.getItem(THEME_KEY) || "auto"; } catch (e) { return "auto"; }
}
export function getAccent() {
  try {
    const a = localStorage.getItem(ACCENT_KEY) || "indigo";
    return ACCENTS.includes(a) ? a : "indigo";
  } catch (e) { return "indigo"; }
}

export function applyTheme(mode) {
  const dark = mode === "dark" || (mode === "auto" && media().matches);
  document.documentElement.classList.toggle("dark", dark);
}
export function applyAccent(accent) {
  const a = ACCENTS.includes(accent) ? accent : "indigo";
  // L'indigo est la valeur par défaut (aucun attribut) ; les autres via data-accent.
  if (a === "indigo") document.documentElement.removeAttribute("data-accent");
  else document.documentElement.setAttribute("data-accent", a);
}

export function setTheme(mode) {
  try { localStorage.setItem(THEME_KEY, mode); } catch (e) { /* no-op */ }
  applyTheme(mode);
  window.dispatchEvent(new Event("vellucast-theme"));
}
export function setAccent(accent) {
  try { localStorage.setItem(ACCENT_KEY, accent); } catch (e) { /* no-op */ }
  applyAccent(accent);
  window.dispatchEvent(new Event("vellucast-theme"));
}

export function initTheme() {
  applyTheme(getTheme());
  applyAccent(getAccent());
  media().addEventListener("change", () => {
    if (getTheme() === "auto") applyTheme("auto");
  });
}
