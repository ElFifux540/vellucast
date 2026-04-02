<template>
  <div class="library-view space-y-6">
    <h1 class="text-2xl font-bold tracking-tight text-slate-900">
      Vellucast — Ma bibliothèque
    </h1>

    <!-- Zone principale : aperçu du média sélectionné -->
    <section
      class="library-hero overflow-hidden rounded-2xl border border-slate-200/90 bg-gradient-to-br from-slate-50 via-white to-indigo-50/40 p-6 shadow-lg ring-1 ring-slate-200/70 sm:p-8"
      aria-label="Aperçu du média"
    >
      <template v-if="previewContent">
        <div
          class="library-banner mb-6 flex min-h-[140px] items-center justify-center rounded-xl border-2 border-dashed border-slate-300/90 bg-slate-100/80 text-center text-sm font-medium text-slate-500"
        >
          Bannière (à venir)
        </div>
        <h2
          class="mb-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl"
        >
          {{ previewContent.title }}
        </h2>
        <p class="mb-6 font-mono text-sm text-slate-600">
          <span class="text-slate-500">ID</span> · {{ previewContent.id }}
        </p>
        <button
          type="button"
          class="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-500/25 transition hover:from-indigo-500 hover:to-violet-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          @click="emitPlay"
        >
          Lecture
        </button>
      </template>
      <div
        v-else
        class="flex min-h-[200px] flex-col items-center justify-center gap-2 text-center"
      >
        <p class="text-base font-medium text-slate-600">
          Sélectionnez un média dans la liste ci-dessous.
        </p>
        <p class="max-w-md text-sm text-slate-500">
          {{
            libraryTab === "series"
              ? "Choisissez un épisode dans une série ci-dessous pour l’aperçu ici, puis Lecture."
              : "Le titre et les informations s’affichent ici ; utilisez Lecture pour ouvrir le lecteur."
          }}
        </p>
      </div>
    </section>

    <!-- Onglets Films / Séries -->
    <div
      class="flex flex-wrap gap-3"
      role="tablist"
      aria-label="Filtrer par type de contenu"
    >
      <button
        type="button"
        role="tab"
        class="library-tab-btn"
        :class="{ 'library-tab-btn--active': libraryTab === 'movies' }"
        :aria-selected="libraryTab === 'movies'"
        @click="libraryTab = 'movies'"
      >
        🎬 Films
      </button>
      <button
        type="button"
        role="tab"
        class="library-tab-btn"
        :class="{ 'library-tab-btn--active': libraryTab === 'series' }"
        :aria-selected="libraryTab === 'series'"
        @click="libraryTab = 'series'"
      >
        📺 Séries
      </button>
    </div>

    <!-- Liste des médias -->
    <div
      class="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg ring-1 ring-slate-200/60"
    >
      <h2 class="mb-1 text-lg font-semibold text-slate-900">Catalogue</h2>
      <p class="mb-4 text-sm text-slate-600">
        {{
          libraryTab === "movies"
            ? "Films disponibles sur votre serveur."
            : "Séries regroupées par nom ; ouvrez une carte pour parcourir saisons et épisodes."
        }}
      </p>

      <p v-if="loading" class="text-slate-600">Chargement…</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>

      <!-- Vue Films -->
      <template v-else-if="libraryTab === 'movies'">
        <p v-if="movieItems.length === 0" class="text-slate-600">
          Aucun film dans cette catégorie.
        </p>
        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <button
            v-for="c in movieItems"
            :key="c.id"
            type="button"
            class="group flex min-h-[5.5rem] flex-col rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4 text-left shadow-sm transition hover:border-indigo-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            :class="{
              'ring-2 ring-indigo-400 border-indigo-300': previewContent?.id === c.id,
            }"
            @click="selectPreview(c)"
            @contextmenu.prevent.stop="openMediaCtx($event, c)"
          >
            <span class="font-semibold text-slate-900 group-hover:text-indigo-800">{{
              c.title
            }}</span>
            <span class="mt-auto truncate pt-2 text-xs text-slate-500">{{ c.id }}</span>
          </button>
        </div>
      </template>

      <!-- Vue Séries : tuiles + accordéons (comme Contenus existants admin) -->
      <template v-else>
        <p v-if="sortedSeriesNames.length === 0" class="library-empty-hint">
          Aucune série détectée. Les épisodes doivent avoir un titre du type « Nom de la série -
          Saison n - … » (comme à la création ou à l’upload).
        </p>
        <div v-else class="library-series-grid">
          <details
            v-for="seriesName in sortedSeriesNames"
            :key="seriesName"
            class="library-series-tile"
          >
            <summary class="library-series-summary">
              <span class="library-series-title">{{ seriesName }}</span>
              <span class="library-series-count">
                {{ episodeCountForSeries(seriesName) }} ép.
              </span>
            </summary>
            <div class="library-series-stack">
              <template v-for="season in sortedSeasonsFor(seriesName)" :key="season">
                <div class="library-season-block">
                  <h4 class="library-season-title">Saison {{ season }}</h4>
                  <ul class="library-episode-list">
                    <li
                      v-for="item in sortedEpisodesFor(seriesName, season)"
                      :key="item.content.id"
                      class="library-episode-item"
                    >
                      <button
                        type="button"
                        class="library-episode-btn"
                        :class="{
                          'library-episode-btn--active':
                            previewContent?.id === item.content.id,
                        }"
                        @click="selectPreview(item.content)"
                        @contextmenu.prevent.stop="openMediaCtx($event, item.content)"
                      >
                        <span class="library-episode-label">{{
                          episodeSummaryLine(item)
                        }}</span>
                        <span class="library-episode-id">{{ item.content.id }}</span>
                      </button>
                    </li>
                  </ul>
                </div>
              </template>
            </div>
          </details>
        </div>
      </template>
    </div>

    <MediaContextMenu
      :visible="ctxOpen"
      :x="ctxX"
      :y="ctxY"
      :content="ctxContent"
      :show-do-not-optimize="isAdmin"
      @close="closeMediaCtx"
      @action="onMediaCtxAction"
    />
  </div>
</template>

<script>
import { API_BASE } from "../config.js";
import MediaContextMenu from "./MediaContextMenu.vue";

/**
 * Cohérent avec Settings (admin) : épisodes reconnus par le motif titre.
 */
function parseSeriesFromTitle(title) {
  const re =
    /^(.+?)\s*-\s*Saison\s+(\d+)\s*-\s*(?:Ép\.\s*(\d+)\s*-\s*)?(.+)$/i;
  const m = (title || "").trim().match(re);
  if (!m) return null;
  return {
    seriesName: m[1].trim(),
    season: parseInt(m[2], 10),
    episode: m[3] != null ? parseInt(m[3], 10) : null,
    remainder: (m[4] || "").trim(),
  };
}

export default {
  name: "Library",
  components: { MediaContextMenu },
  props: {
    token: {
      type: String,
      required: true,
    },
    isAdmin: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["play"],
  data() {
    return {
      items: [],
      loading: true,
      error: "",
      libraryTab: "movies",
      previewContent: null,
      ctxOpen: false,
      ctxX: 0,
      ctxY: 0,
      ctxContent: null,
    };
  },
  computed: {
    movieItems() {
      const list = this.items || [];
      return list.filter((c) => !parseSeriesFromTitle(c.title));
    },
    seriesItems() {
      const list = this.items || [];
      return list.filter((c) => parseSeriesFromTitle(c.title));
    },
    seriesTree() {
      const tree = {};
      for (const c of this.seriesItems) {
        const p = parseSeriesFromTitle(c.title);
        if (!p) continue;
        const name = p.seriesName;
        if (!tree[name]) tree[name] = {};
        if (!tree[name][p.season]) tree[name][p.season] = [];
        tree[name][p.season].push({ ...p, content: c });
      }
      return tree;
    },
    sortedSeriesNames() {
      return Object.keys(this.seriesTree).sort((a, b) =>
        a.localeCompare(b, "fr", { sensitivity: "base" }),
      );
    },
  },
  watch: {
    libraryTab() {
      if (!this.previewContent) return;
      const ok =
        this.libraryTab === "movies"
          ? this.movieItems.some((c) => c.id === this.previewContent.id)
          : this.seriesItems.some((c) => c.id === this.previewContent.id);
      if (!ok) this.previewContent = null;
    },
  },
  async mounted() {
    await this.fetchContents();
  },
  methods: {
    sortedSeasonsFor(seriesName) {
      return Object.keys(this.seriesTree[seriesName] || {})
        .map(Number)
        .sort((a, b) => a - b);
    },
    sortedEpisodesFor(seriesName, season) {
      const arr = [...(this.seriesTree[seriesName]?.[season] || [])];
      return arr.sort((a, b) => {
        if (a.episode != null && b.episode != null) {
          return a.episode - b.episode;
        }
        if (a.episode != null) return -1;
        if (b.episode != null) return 1;
        return (a.content.title || "").localeCompare(b.content.title || "", "fr");
      });
    },
    episodeSummaryLine(item) {
      if (item.episode != null) {
        return `Ép. ${item.episode} — ${item.remainder || item.content.title}`;
      }
      return item.remainder || item.content.title;
    },
    episodeCountForSeries(seriesName) {
      const seasons = this.seriesTree[seriesName] || {};
      return Object.values(seasons).reduce((acc, arr) => acc + arr.length, 0);
    },
    async fetchContents() {
      this.loading = true;
      this.error = "";
      try {
        const response = await fetch(`${API_BASE}/contents`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          this.error = body.detail || `Erreur ${response.status}`;
          this.items = [];
          return;
        }
        const data = await response.json();
        this.items = Array.isArray(data) ? data : [];
      } catch (e) {
        this.error = "Impossible de joindre le serveur.";
        this.items = [];
      } finally {
        this.loading = false;
      }
    },
    selectPreview(c) {
      this.previewContent = c;
    },
    emitPlay() {
      if (!this.previewContent) return;
      this.$emit("play", this.previewContent);
    },
    openMediaCtx(event, content) {
      this.ctxX = event.clientX;
      this.ctxY = event.clientY;
      this.ctxContent = content;
      this.ctxOpen = true;
    },
    closeMediaCtx() {
      this.ctxOpen = false;
      this.ctxContent = null;
    },
    onMediaCtxAction({ type, content }) {
      if (type === "no_optimize") {
        this.toggleDoNotOptimize(content);
        return;
      }
      console.log(`[Vellucast contexte] ${type}`, { id: content?.id, content });
    },
    async toggleDoNotOptimize(content) {
      if (!this.isAdmin || !content?.id) return;
      try {
        const response = await fetch(
          `${API_BASE}/api/contents/${encodeURIComponent(content.id)}/toggle-optimize`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${this.token}`,
            },
          },
        );
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          console.warn("[do_not_optimize]", data?.detail || data);
          return;
        }
        const nextFlag =
          data && Object.prototype.hasOwnProperty.call(data, "do_not_optimize")
            ? Boolean(data.do_not_optimize)
            : !Boolean(content.do_not_optimize);
        const patchRow = (row) =>
          row && row.id === content.id
            ? { ...row, do_not_optimize: nextFlag }
            : row;
        this.items = (this.items || []).map(patchRow);
        if (this.previewContent?.id === content.id) {
          this.previewContent = patchRow(this.previewContent);
        }
      } catch (e) {
        console.error("[do_not_optimize]", e);
      }
    },
  },
};
</script>

<style scoped>
.library-tab-btn {
  flex: 1;
  min-width: 10rem;
  padding: 0.85rem 1.25rem;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.library-tab-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.library-tab-btn--active {
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  border-color: #a5b4fc;
  color: #1e1b4b;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.15);
}

/* Catalogue séries (aligné sur Settings / Contenus existants) */
.library-empty-hint {
  margin: 0 0 0.5rem;
  padding: 1rem 1.1rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.45;
}

.library-series-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: 1rem;
  align-items: start;
}

.library-series-tile {
  border-radius: 14px;
  border: 1px solid #c7d2fe;
  background: linear-gradient(180deg, #fafaff 0%, #ffffff 100%);
  box-shadow:
    0 4px 18px rgba(99, 102, 241, 0.08),
    0 1px 3px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.library-series-tile[open] {
  border-color: #a5b4fc;
  box-shadow:
    0 8px 28px rgba(99, 102, 241, 0.12),
    0 2px 8px rgba(15, 23, 42, 0.06);
}

.library-series-tile > summary {
  list-style: none;
  cursor: pointer;
  user-select: none;
}

.library-series-tile > summary::-webkit-details-marker {
  display: none;
}

.library-series-summary {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem 1rem;
  padding: 1rem 1.15rem 1rem 2.75rem;
  font-weight: 600;
  color: #312e81;
}

.library-series-summary::before {
  content: "▸";
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #818cf8;
  font-size: 0.9rem;
  transition: transform 0.2s ease;
}

.library-series-tile[open] > .library-series-summary::before {
  transform: translateY(-50%) rotate(90deg);
}

.library-series-title {
  font-size: 1.05rem;
  line-height: 1.35;
  flex: 1;
  min-width: 0;
}

.library-series-count {
  flex-shrink: 0;
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
}

.library-series-stack {
  padding: 0 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-top: 1px solid #eef2ff;
}

.library-season-block {
  margin: 0;
}

.library-season-title {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6366f1;
}

.library-episode-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.library-episode-item {
  margin: 0;
}

.library-episode-btn {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  text-align: left;
  padding: 0.65rem 0.75rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #1e293b;
  font-size: 0.92rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.library-episode-btn:focus-visible {
  outline: 2px solid #6366f1;
  outline-offset: 2px;
}

.library-episode-btn:hover {
  border-color: #c7d2fe;
  background: #fafaff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
}

.library-episode-btn--active {
  border-color: #818cf8;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.25);
}

.library-episode-label {
  line-height: 1.35;
}

.library-episode-id {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.72rem;
  color: #64748b;
}
</style>
