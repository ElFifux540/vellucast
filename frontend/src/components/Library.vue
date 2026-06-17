<template>
  <div class="library-view" :style="{ '--poster-min': posterMin }">
    <!-- Barre de recherche (les résultats s'affichent dans la bibliothèque ci-dessous) -->
    <div class="lib-search">
      <div class="lib-search-box">
        <span class="lib-search-icon">🔍</span>
        <input
          v-model="searchQuery"
          type="search"
          class="lib-search-input"
          placeholder="Rechercher un film, une série…"
          aria-label="Rechercher"
          @input="onSearchInput"
        />
        <span v-if="searching || externalSearching" class="lib-search-spinner">…</span>
        <button
          v-if="searchQuery"
          type="button"
          class="lib-search-clear"
          title="Effacer la recherche"
          @click="clearSearchQuery"
        >
          ✕
        </button>
      </div>
    </div>

    <!-- Hero / bannière : affiché seulement quand un média est sélectionné (animation douce) -->
    <transition name="lib-hero-anim">
      <section v-if="previewContent" class="lib-hero" :style="heroStyle">
        <button
          type="button"
          class="lib-hero-close"
          title="Fermer l'aperçu"
          @click="previewContent = null"
        >
          ✕
        </button>
        <div class="lib-hero-inner">
          <img
            v-if="previewContent.poster_url"
            :src="previewContent.poster_url"
            :alt="previewContent.title"
            class="lib-hero-poster"
          />
          <div class="lib-hero-text">
            <h1 class="lib-hero-title">{{ previewContent.title }}</h1>
            <p class="lib-hero-meta">
              <span v-if="previewContent.year">{{ previewContent.year }}</span>
              <span v-if="previewContent.media_type" class="lib-pill">
                {{ previewContent.media_type === "tv" ? "Série" : "Film" }}
              </span>
            </p>
            <p v-if="previewContent.overview" class="lib-hero-overview">
              {{ previewContent.overview }}
            </p>
            <div class="lib-hero-actions">
              <button type="button" class="lib-btn-play" @click="emitPlay">▶ Lecture</button>
              <button type="button" class="lib-btn-ghost" @click="openInfo(previewContent)">
                Plus d'infos
              </button>
            </div>
          </div>
        </div>
      </section>
    </transition>

    <p v-if="loading" class="lib-state">Chargement…</p>
    <p v-else-if="error" class="lib-state lib-state--error">{{ error }}</p>

    <!-- Mode recherche : résultats affichés directement dans la bibliothèque -->
    <template v-else-if="isSearching">
      <div class="lib-results-head">
        <h2 class="lib-results-title">Résultats pour « {{ searchQuery }} »</h2>
        <button type="button" class="lib-results-clear" @click="clearSearchQuery">Effacer</button>
      </div>

      <p class="lib-search-section">Ma bibliothèque</p>
      <p v-if="searching && !searchResults.length" class="lib-state">Recherche…</p>
      <div v-else-if="searchResults.length" class="lib-poster-grid">
        <button
          v-for="c in searchResults"
          :key="c.id"
          type="button"
          class="lib-poster-card"
          :class="{ 'lib-poster-card--active': previewContent && previewContent.id === c.id }"
          @click="selectPreview(c)"
          @dblclick="$emit('play', c)"
          @contextmenu.prevent.stop="openMediaCtx($event, c)"
        >
          <div class="lib-poster-img-wrap">
            <img v-if="c.poster_url" :src="c.poster_url" :alt="c.title" class="lib-poster-img" loading="lazy" />
            <div v-else class="lib-poster-placeholder"><span>{{ c.title }}</span></div>
            <span class="lib-poster-hover">▶</span>
          </div>
          <span class="lib-poster-caption">{{ c.title }}</span>
        </button>
      </div>
      <p v-else class="lib-state">Aucun média dans votre bibliothèque.</p>

      <template v-if="externalResults.length">
        <p class="lib-search-section">
          Sur Overseerr <span v-if="externalSearching" class="lib-search-spinner">…</span>
        </p>
        <div class="lib-poster-grid">
          <button
            v-for="r in externalResults"
            :key="'ext-' + r.media_type + '-' + r.id"
            type="button"
            class="lib-poster-card"
            @click="onExternalResultClick(r)"
          >
            <div class="lib-poster-img-wrap">
              <img v-if="r.poster_url" :src="r.poster_url" :alt="r.title" class="lib-poster-img" loading="lazy" />
              <div v-else class="lib-poster-placeholder"><span>{{ r.title }}</span></div>
              <span class="lib-poster-ext">Externe</span>
            </div>
            <span class="lib-poster-caption">
              {{ r.title }}<template v-if="r.year"> ({{ r.year }})</template>
            </span>
          </button>
        </div>
      </template>
      <p v-else-if="externalSearching" class="lib-search-section">Recherche Overseerr…</p>
    </template>

    <!-- Mode normal : onglets + grilles -->
    <template v-else>
      <div class="lib-toolbar">
        <div class="lib-tabs" role="tablist">
          <button
            type="button"
            class="lib-tab"
            :class="{ 'lib-tab--active': libraryTab === 'movies' }"
            @click="switchTab('movies')"
          >
            🎬 Films <span class="lib-tab-count">{{ movieItems.length }}</span>
          </button>
          <button
            type="button"
            class="lib-tab"
            :class="{ 'lib-tab--active': libraryTab === 'series' }"
            @click="switchTab('series')"
          >
            📺 Séries <span class="lib-tab-count">{{ sortedSeriesNames.length }}</span>
          </button>
        </div>
        <div v-if="isAdmin" class="lib-toolbar-actions">
          <button
            v-if="libraryTab === 'movies'"
            type="button"
            class="lib-add-btn"
            @click="dashboardApp.showUploadModal = true"
          >
            ➕ Ajouter un film
          </button>
          <button v-else type="button" class="lib-add-btn" @click="openSeriesUploadNew">
            ➕ Nouvelle série / épisodes
          </button>
        </div>
      </div>

      <!-- Films : grille d'affiches -->
      <template v-if="libraryTab === 'movies'">
        <p v-if="movieItems.length === 0" class="lib-state">Aucun film.</p>
        <div v-else class="lib-poster-grid">
          <button
            v-for="c in movieItems"
            :key="c.id"
            type="button"
            class="lib-poster-card"
            :class="{ 'lib-poster-card--active': previewContent && previewContent.id === c.id }"
            @click="selectPreview(c)"
            @dblclick="$emit('play', c)"
            @contextmenu.prevent.stop="openMediaCtx($event, c)"
          >
            <div class="lib-poster-img-wrap">
              <img v-if="c.poster_url" :src="c.poster_url" :alt="c.title" class="lib-poster-img" loading="lazy" />
              <div v-else class="lib-poster-placeholder">
                <span>{{ c.title }}</span>
              </div>
              <span class="lib-poster-hover">▶</span>
            </div>
            <span class="lib-poster-caption">{{ c.title }}</span>
          </button>
        </div>
      </template>

      <!-- Séries : grille d'affiches → vue détail (saisons puis épisodes) -->
      <template v-else>
        <SeriesDetail
          v-if="openedSeries"
          :series-name="openedSeries"
          :episodes="episodesOfSeries(openedSeries)"
          :series-meta="seriesMetadata(openedSeries)"
          :poster-min="posterMin"
          :is-admin="isAdmin"
          @back="openedSeries = ''"
          @play="$emit('play', $event)"
          @context="onSeriesEpisodeContext"
          @add-episodes="openAddEpisode(openedSeries)"
        />
        <template v-else>
          <p v-if="sortedSeriesNames.length === 0" class="lib-state">
            Aucune série. Utilisez « Nouvelle série / épisodes » pour en ajouter (format « Nom - S01E01 »).
          </p>
          <div v-else class="lib-poster-grid">
            <button
              v-for="seriesName in sortedSeriesNames"
              :key="seriesName"
              type="button"
              class="lib-poster-card"
              @click="openSeries(seriesName)"
              @contextmenu.prevent.stop="openSeriesCtx($event, seriesName)"
            >
              <div class="lib-poster-img-wrap">
                <img
                  v-if="seriesPoster(seriesName)"
                  :src="seriesPoster(seriesName)"
                  :alt="seriesName"
                  class="lib-poster-img"
                  loading="lazy"
                />
                <div v-else class="lib-poster-placeholder"><span>{{ seriesName }}</span></div>
                <span class="lib-poster-hover">▶</span>
                <span class="lib-series-eps">{{ episodeCountForSeries(seriesName) }} ép.</span>
              </div>
              <span class="lib-poster-caption">{{ seriesName }}</span>
            </button>
          </div>
        </template>
      </template>
    </template>

    <MediaContextMenu
      :visible="ctxOpen"
      :x="ctxX"
      :y="ctxY"
      :content="ctxContent"
      :show-do-not-optimize="isAdmin"
      @close="closeMediaCtx"
      @action="onMediaCtxAction"
    />

    <MediaInfoModal
      v-if="infoContent"
      :content="infoContent"
      :is-admin="isAdmin"
      @close="infoContent = null"
      @updated="onContentUpdated"
      @associate="openAssocFromInfo"
    />

    <AssociationModal
      v-if="assocTarget || assocSeries"
      :initial-query="assocInitialQuery"
      :media-type="assocMediaType"
      @close="closeAssociation"
      @associated="onAssociated"
    />

    <SeriesContextMenu
      :visible="seriesCtxOpen"
      :x="seriesCtxX"
      :y="seriesCtxY"
      :series-name="seriesCtxName"
      :merge-candidates="seriesCtxCandidates"
      @close="seriesCtxOpen = false"
      @action="onSeriesCtxAction"
    />

    <SeriesUploadModal
      v-if="showSeriesUpload"
      :existing-series="existingSeriesList"
      :preset-name="seriesUploadPreset"
      :preset-metadata="seriesUploadPresetMeta"
      @close="showSeriesUpload = false"
      @done="onSeriesUploadDone"
    />
  </div>
</template>

<script>
import { API_BASE } from "../config.js";
import MediaContextMenu from "./MediaContextMenu.vue";
import MediaInfoModal from "./MediaInfoModal.vue";
import AssociationModal from "./AssociationModal.vue";
import SeriesContextMenu from "./SeriesContextMenu.vue";
import SeriesUploadModal from "./SeriesUploadModal.vue";
import SeriesDetail from "./SeriesDetail.vue";

function parseSeriesFromTitle(title) {
  const t = (title || "").trim();

  // Format compact SxxEyy : « Nom - S01E01 », « Nom S01E01 » (+ éventuel titre d'épisode).
  let m = t.match(/^(.+?)[\s-]+S(\d{1,2})E(\d{1,2})\b[\s-]*(.*)$/i);
  if (m) {
    return {
      seriesName: m[1].trim().replace(/[\s-]+$/, ""),
      season: parseInt(m[2], 10),
      episode: parseInt(m[3], 10),
      remainder: (m[4] || "").trim(),
    };
  }

  // Format « Nom - Saison N - Ép. M - reste » ou « Nom - Saison N - reste ».
  m = t.match(/^(.+?)\s*-\s*Saison\s+(\d+)\s*-\s*(?:Ép\.\s*(\d+)\s*-\s*)?(.+)$/i);
  if (m) {
    return {
      seriesName: m[1].trim(),
      season: parseInt(m[2], 10),
      episode: m[3] != null ? parseInt(m[3], 10) : null,
      remainder: (m[4] || "").trim(),
    };
  }

  return null;
}

export default {
  // Bibliothèque type Plex : affiches, hero/bannière, omnibox, menu contextuel.
  name: "Library",
  components: {
    MediaContextMenu,
    MediaInfoModal,
    AssociationModal,
    SeriesContextMenu,
    SeriesUploadModal,
    SeriesDetail,
  },
  inject: ["dashboardApp"],
  props: {
    token: { type: String, required: true },
    isAdmin: { type: Boolean, default: false },
  },
  emits: ["play"],
  data() {
    // État de la bibliothèque, de l'omnibox et des modales.
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
      // Recherche omnibox
      searchQuery: "",
      searchResults: [],
      searching: false,
      searchDone: false,
      showSearch: false,
      searchTimer: null,
      // Suggestions externes (Overseerr) dans l'omnibox
      externalResults: [],
      externalSearching: false,
      externalTimer: null,
      // Modales
      infoContent: null,
      assocTarget: null,
      assocSeries: null,
      assocInitialQuery: "",
      assocMediaType: "",
      // Menu contextuel de série + ajout d'épisode
      seriesCtxOpen: false,
      seriesCtxX: 0,
      seriesCtxY: 0,
      seriesCtxName: "",
      seriesCtxCandidates: [],
      openedSeries: "",
      showSeriesUpload: false,
      seriesUploadPreset: "",
      seriesUploadPresetMeta: {},
      posterSize: "medium",
    };
  },
  computed: {
    movieItems() {
      return (this.items || []).filter((c) => !parseSeriesFromTitle(c.title));
    },
    seriesItems() {
      return (this.items || []).filter((c) => parseSeriesFromTitle(c.title));
    },
    seriesTree() {
      const tree = {};
      for (const c of this.seriesItems) {
        const p = parseSeriesFromTitle(c.title);
        if (!p) continue;
        if (!tree[p.seriesName]) tree[p.seriesName] = {};
        if (!tree[p.seriesName][p.season]) tree[p.seriesName][p.season] = [];
        tree[p.seriesName][p.season].push({ ...p, content: c });
      }
      return tree;
    },
    sortedSeriesNames() {
      return Object.keys(this.seriesTree).sort((a, b) =>
        a.localeCompare(b, "fr", { sensitivity: "base" }),
      );
    },
    heroStyle() {
      const bg = this.previewContent && this.previewContent.backdrop_url;
      if (bg) {
        return {
          backgroundImage: `linear-gradient(to right, rgba(15,23,42,0.92) 0%, rgba(15,23,42,0.6) 60%, rgba(15,23,42,0.4) 100%), url("${bg}")`,
        };
      }
      return {};
    },
    isSearching() {
      return !!this.searchQuery.trim();
    },
    posterMin() {
      return { small: "110px", medium: "140px", large: "190px" }[this.posterSize] || "140px";
    },
    existingSeriesList() {
      // Pour le modal d'ajout : séries déjà enregistrées + leurs métadonnées d'association.
      return this.sortedSeriesNames.map((name) => ({
        name,
        metadata: this.seriesMetadata(name),
      }));
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
    this.loadPosterSize();
    await this.fetchContents();
    document.addEventListener("click", this.onDocClick);
    window.addEventListener("vellucast-poster-size", this.loadPosterSize);
    window.addEventListener("vellucast-contents-changed", this.fetchContents);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.onDocClick);
    window.removeEventListener("vellucast-poster-size", this.loadPosterSize);
    window.removeEventListener("vellucast-contents-changed", this.fetchContents);
  },
  methods: {
    loadPosterSize() {
      try {
        const saved = localStorage.getItem("vellucast_poster_size");
        if (saved && ["small", "medium", "large"].includes(saved)) this.posterSize = saved;
      } catch (e) {
        /* no-op */
      }
    },
    onDocClick(e) {
      if (!this.$el.querySelector(".lib-search")?.contains(e.target)) {
        this.showSearch = false;
      }
    },
    sortedSeasonsFor(seriesName) {
      return Object.keys(this.seriesTree[seriesName] || {})
        .map(Number)
        .sort((a, b) => a - b);
    },
    sortedEpisodesFor(seriesName, season) {
      const arr = [...(this.seriesTree[seriesName]?.[season] || [])];
      return arr.sort((a, b) => {
        if (a.episode != null && b.episode != null) return a.episode - b.episode;
        if (a.episode != null) return -1;
        if (b.episode != null) return 1;
        return (a.content.title || "").localeCompare(b.content.title || "", "fr");
      });
    },
    episodeSummaryLine(item) {
      if (item.episode != null) {
        // Pas de titre d'épisode (format SxxEyy seul) → on affiche juste « Épisode N ».
        return item.remainder ? `Ép. ${item.episode} — ${item.remainder}` : `Épisode ${item.episode}`;
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
    // --- Omnibox ---
    onSearchInput() {
      if (this.searchTimer) clearTimeout(this.searchTimer);
      if (this.externalTimer) clearTimeout(this.externalTimer);
      const q = this.searchQuery.trim();
      if (!q) {
        this.searchResults = [];
        this.externalResults = [];
        this.searchDone = false;
        this.externalSearching = false;
        return;
      }
      // Recherche locale rapide (250 ms) puis suggestions Overseerr après ~2 s d'inactivité.
      this.searchTimer = setTimeout(() => this.runSearch(), 250);
      this.externalResults = [];
      this.externalTimer = setTimeout(() => this.runExternalSearch(), 2000);
    },
    clearSearchQuery() {
      this.searchQuery = "";
      this.searchResults = [];
      this.externalResults = [];
      this.searchDone = false;
      this.searching = false;
      this.externalSearching = false;
      if (this.searchTimer) clearTimeout(this.searchTimer);
      if (this.externalTimer) clearTimeout(this.externalTimer);
    },
    normTitle(s) {
      // Normalise un titre pour comparaison : minuscules, sans année ni ponctuation.
      return String(s || "")
        .toLowerCase()
        .replace(/\b(19|20)\d{2}\b/g, "")
        .replace(/[^a-z0-9]/g, "");
    },
    localMatchKeys() {
      // Clés des films déjà présents (titres normalisés + tmdb_id), pour filtrer l'externe.
      const titles = new Set();
      const tmdb = new Set();
      for (const c of this.items || []) {
        if (parseSeriesFromTitle(c.title)) continue; // les épisodes ne polluent pas les films
        if (c.title) titles.add(this.normTitle(c.title));
        if (c.tmdb_id) tmdb.add(String(c.tmdb_id));
      }
      return { titles, tmdb };
    },
    async runExternalSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;
      this.externalSearching = true;
      try {
        const url = `${API_BASE}/api/search/external?q=${encodeURIComponent(q)}`;
        const res = await fetch(url, { headers: { Authorization: `Bearer ${this.token}` } });
        const data = await res.json().catch(() => ({}));
        let items = res.ok && Array.isArray(data.items) ? data.items : [];
        // On masque les suggestions déjà présentes dans la bibliothèque (titre ou tmdb_id).
        const { titles, tmdb } = this.localMatchKeys();
        items = items.filter(
          (r) => !tmdb.has(String(r.tmdb_id)) && !titles.has(this.normTitle(r.title)),
        );
        this.externalResults = items.slice(0, 8);
      } catch (e) {
        this.externalResults = [];
      } finally {
        this.externalSearching = false;
      }
    },
    async runSearch() {
      const q = this.searchQuery.trim();
      if (!q) return;
      this.searching = true;
      try {
        const url = `${API_BASE}/api/search/library?q=${encodeURIComponent(q)}&limit=12`;
        const res = await fetch(url, { headers: { Authorization: `Bearer ${this.token}` } });
        const data = await res.json().catch(() => ({}));
        this.searchResults = res.ok && Array.isArray(data.items) ? data.items : [];
        this.searchDone = true;
      } catch (e) {
        this.searchResults = [];
      } finally {
        this.searching = false;
      }
    },
    onSearchResultClick(r) {
      this.selectPreview(r);
      const isSeries = !!parseSeriesFromTitle(r.title);
      this.libraryTab = isSeries ? "series" : "movies";
      this.closeSearch();
    },
    playFirstResult() {
      if (this.searchResults.length) {
        this.$emit("play", this.searchResults[0]);
        this.closeSearch();
      }
    },
    onExternalResultClick(r) {
      // Résultat externe : pas de fichier local, mais on affiche ses infos (affiche, synopsis…).
      this.infoContent = {
        id: null,
        title: r.title,
        media_path: "",
        overview: r.overview || "",
        year: r.year != null ? String(r.year) : "",
        poster_url: r.poster_url || "",
        backdrop_url: r.backdrop_url || "",
        media_type: r.media_type || "",
        tmdb_id: r.tmdb_id != null ? String(r.tmdb_id) : "",
        __external: true,
      };
      this.closeSearch();
    },
    closeSearch() {
      this.showSearch = false;
      if (this.externalTimer) clearTimeout(this.externalTimer);
    },
    // --- Sélection / lecture ---
    selectPreview(c) {
      // On reprend la version à jour depuis items si dispo (métadonnées complètes).
      const fresh = (this.items || []).find((x) => x.id === c.id);
      this.previewContent = fresh || c;
    },
    emitPlay() {
      if (this.previewContent) this.$emit("play", this.previewContent);
    },
    // --- Menu contextuel ---
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
      } else if (type === "info" || type === "banner") {
        this.openInfo(content);
      } else if (type === "overseerr") {
        this.openAssociation(content);
      } else if (type === "delete") {
        this.deleteContent(content);
      }
    },
    async deleteContent(content) {
      if (!this.isAdmin || !content?.id) return;
      const ok = window.confirm(`Supprimer « ${content.title} » de la bibliothèque ?`);
      if (!ok) return;
      try {
        const res = await fetch(`${API_BASE}/contents/${encodeURIComponent(content.id)}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${this.token}` },
        });
        if (res.ok) {
          if (this.previewContent && this.previewContent.id === content.id) this.previewContent = null;
          if (this.infoContent && this.infoContent.id === content.id) this.infoContent = null;
          await this.fetchContents();
        }
      } catch (e) {
        /* silencieux */
      }
    },
    // --- Modales infos / association ---
    openInfo(content) {
      const fresh = (this.items || []).find((x) => x.id === content.id) || content;
      this.infoContent = fresh;
    },
    openAssociation(content) {
      this.assocSeries = null;
      this.assocTarget = content;
      this.assocInitialQuery = this.cleanTitleForQuery(content.title);
      // Un épisode (titre série) → on cherche une série ; sinon un film.
      this.assocMediaType = parseSeriesFromTitle(content.title) ? "tv" : "movie";
    },
    openSeriesAssociation(seriesName) {
      this.assocTarget = null;
      this.assocSeries = seriesName;
      this.assocInitialQuery = seriesName;
      this.assocMediaType = "tv";
    },
    closeAssociation() {
      this.assocTarget = null;
      this.assocSeries = null;
    },
    onAssociated(payload) {
      if (this.assocSeries) this.applySeriesAssociation(payload);
      else this.applyAssociation(payload);
    },
    openAssocFromInfo() {
      if (this.infoContent) this.openAssociation(this.infoContent);
    },
    // Affiche/bannière d'une série = celle du 1er épisode associé qui en possède une.
    seriesPoster(seriesName) {
      const ep = (this.seriesItems || []).find((c) => {
        const p = parseSeriesFromTitle(c.title);
        return p && p.seriesName === seriesName && c.poster_url;
      });
      return ep ? ep.poster_url : "";
    },
    async applySeriesAssociation({ metadata }) {
      const name = this.assocSeries;
      if (!name) return;
      const episodes = (this.seriesItems || []).filter((c) => {
        const p = parseSeriesFromTitle(c.title);
        return p && p.seriesName === name;
      });
      // On applique les mêmes métadonnées à tous les épisodes (sans toucher aux titres).
      try {
        await Promise.all(
          episodes.map((ep) =>
            fetch(`${API_BASE}/contents/${encodeURIComponent(ep.id)}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
              body: JSON.stringify(metadata),
            }),
          ),
        );
        await this.fetchContents();
      } catch (e) {
        /* best-effort */
      } finally {
        this.assocSeries = null;
      }
    },
    // Liste des épisodes (objets content) d'une série donnée.
    episodesOfSeries(name) {
      return (this.seriesItems || []).filter((c) => {
        const p = parseSeriesFromTitle(c.title);
        return p && p.seriesName === name;
      });
    },
    // Métadonnées d'association d'une série (depuis le 1er épisode qui en possède).
    seriesMetadata(name) {
      const ep = this.episodesOfSeries(name).find((c) => c.tmdb_id || c.poster_url);
      if (!ep) return {};
      const meta = {};
      for (const k of ["poster_url", "backdrop_url", "overview", "year", "tmdb_id", "media_type"]) {
        if (ep[k]) meta[k] = ep[k];
      }
      return meta;
    },
    // Autres séries fusionnables : même nom normalisé OU même tmdb_id associé.
    mergeCandidatesFor(name) {
      const meta = this.seriesMetadata(name);
      const myNorm = this.normTitle(name);
      const myTmdb = meta.tmdb_id ? String(meta.tmdb_id) : "";
      return this.sortedSeriesNames.filter((other) => {
        if (other === name) return false;
        if (this.normTitle(other) === myNorm) return true;
        const oMeta = this.seriesMetadata(other);
        return myTmdb && oMeta.tmdb_id && String(oMeta.tmdb_id) === myTmdb;
      });
    },
    openSeriesCtx(event, seriesName) {
      this.seriesCtxX = event.clientX;
      this.seriesCtxY = event.clientY;
      this.seriesCtxName = seriesName;
      this.seriesCtxCandidates = this.mergeCandidatesFor(seriesName);
      this.seriesCtxOpen = true;
    },
    onSeriesCtxAction({ type, seriesName, target }) {
      if (type === "associate") {
        this.openSeriesAssociation(seriesName);
      } else if (type === "add-episode") {
        this.openAddEpisode(seriesName);
      } else if (type === "merge") {
        this.mergeSeries(seriesName, target);
      } else if (type === "delete-series") {
        this.deleteSeries(seriesName);
      }
    },
    switchTab(tab) {
      this.libraryTab = tab;
      this.openedSeries = "";
    },
    openSeries(name) {
      this.openedSeries = name;
    },
    onSeriesEpisodeContext(event, content) {
      this.openMediaCtx(event, content);
    },
    openSeriesUploadNew() {
      this.seriesUploadPreset = "";
      this.seriesUploadPresetMeta = {};
      this.showSeriesUpload = true;
    },
    // « Ajouter des épisodes » à une série existante (depuis le menu série ou la vue détail).
    openAddEpisode(seriesName) {
      this.seriesUploadPreset = seriesName;
      this.seriesUploadPresetMeta = this.seriesMetadata(seriesName);
      this.showSeriesUpload = true;
    },
    async onSeriesUploadDone() {
      this.showSeriesUpload = false;
      this.seriesUploadPreset = "";
      this.seriesUploadPresetMeta = {};
      await this.fetchContents();
    },
    async mergeSeries(sourceName, targetName) {
      if (!sourceName || !targetName) return;
      const targetMeta = this.seriesMetadata(targetName);
      const episodes = this.episodesOfSeries(sourceName);
      // On renomme chaque épisode source sous le nom de la série cible (en gardant SxxEyy)
      // et on lui applique les métadonnées de la cible.
      const pad2 = (n) => String(Math.max(0, parseInt(n, 10) || 0)).padStart(2, "0");
      try {
        await Promise.all(
          episodes.map((ep) => {
            const p = parseSeriesFromTitle(ep.title) || {};
            let title;
            if (p.episode != null) {
              title = `${targetName} - S${pad2(p.season)}E${pad2(p.episode)}`;
            } else {
              title = `${targetName} - Saison ${p.season || 1} - ${p.remainder || ep.title}`;
            }
            return fetch(`${API_BASE}/contents/${encodeURIComponent(ep.id)}`, {
              method: "PATCH",
              headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
              body: JSON.stringify({ title, ...targetMeta }),
            });
          }),
        );
        await this.fetchContents();
      } catch (e) {
        /* best-effort */
      }
    },
    async deleteSeries(seriesName) {
      const episodes = this.episodesOfSeries(seriesName);
      if (!episodes.length) return;
      const ok = window.confirm(
        `Supprimer la série « ${seriesName} » et ses ${episodes.length} épisode(s) ?`,
      );
      if (!ok) return;
      try {
        await Promise.all(
          episodes.map((ep) =>
            fetch(`${API_BASE}/contents/${encodeURIComponent(ep.id)}`, {
              method: "DELETE",
              headers: { Authorization: `Bearer ${this.token}` },
            }),
          ),
        );
        if (this.previewContent && episodes.some((e) => e.id === this.previewContent.id)) {
          this.previewContent = null;
        }
        await this.fetchContents();
      } catch (e) {
        /* silencieux */
      }
    },
    cleanTitleForQuery(title) {
      const p = parseSeriesFromTitle(title);
      if (p) return p.seriesName;
      return (title || "").replace(/\b(19|20)\d{2}\b/g, "").replace(/[._]/g, " ").trim();
    },
    async applyAssociation({ metadata, matchTitle, applyTitle }) {
      const target = this.assocTarget;
      if (!target) return;
      const body = { ...metadata };
      if (applyTitle && matchTitle && !parseSeriesFromTitle(target.title)) {
        body.title = matchTitle;
      }
      try {
        const res = await fetch(`${API_BASE}/contents/${encodeURIComponent(target.id)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
          body: JSON.stringify(body),
        });
        if (res.ok) {
          await this.fetchContents();
          this.refreshOpenModals(target.id);
        }
      } catch (e) {
        /* silencieux */
      } finally {
        this.assocTarget = null;
      }
    },
    refreshOpenModals(id) {
      const fresh = (this.items || []).find((x) => x.id === id);
      if (!fresh) return;
      if (this.infoContent && this.infoContent.id === id) this.infoContent = fresh;
      if (this.previewContent && this.previewContent.id === id) this.previewContent = fresh;
    },
    async onContentUpdated() {
      const id = this.infoContent?.id;
      await this.fetchContents();
      if (id) this.refreshOpenModals(id);
    },
    async toggleDoNotOptimize(content) {
      if (!this.isAdmin || !content?.id) return;
      try {
        const response = await fetch(
          `${API_BASE}/api/contents/${encodeURIComponent(content.id)}/toggle-optimize`,
          { method: "POST", headers: { Authorization: `Bearer ${this.token}` } },
        );
        const data = await response.json().catch(() => ({}));
        if (!response.ok) return;
        const nextFlag =
          data && Object.prototype.hasOwnProperty.call(data, "do_not_optimize")
            ? Boolean(data.do_not_optimize)
            : !Boolean(content.do_not_optimize);
        const patchRow = (row) =>
          row && row.id === content.id ? { ...row, do_not_optimize: nextFlag } : row;
        this.items = (this.items || []).map(patchRow);
        if (this.previewContent?.id === content.id) this.previewContent = patchRow(this.previewContent);
      } catch (e) {
        /* silencieux */
      }
    },
  },
};
</script>

<style scoped>
.library-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* --- Omnibox --- */
.lib-search {
  position: relative;
  z-index: 40;
}

.lib-search-box {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 14px;
  padding: 0.65rem 1rem;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
}

.lib-search-box:focus-within {
  border-color: #a5b4fc;
  box-shadow: 0 4px 18px rgba(99, 102, 241, 0.18);
}

.lib-search-icon {
  opacity: 0.6;
}

.lib-search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 1rem;
  background: transparent;
}

.lib-search-spinner {
  color: #6366f1;
}

.lib-search-clear {
  border: none;
  background: #e2e8f0;
  color: #475569;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.8rem;
  line-height: 1;
  flex-shrink: 0;
}

.lib-search-clear:hover {
  background: #cbd5e1;
}

.lib-results-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.lib-results-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.lib-results-clear {
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  border-radius: 10px;
  padding: 0.45rem 0.9rem;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

.lib-results-clear:hover {
  background: #f1f5f9;
}

.lib-poster-ext {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #b45309;
  background: #fef3c7;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.lib-search-dropdown {
  position: absolute;
  top: calc(100% + 0.4rem);
  left: 0;
  right: 0;
  margin: 0;
  padding: 0.4rem;
  list-style: none;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.18);
  max-height: 26rem;
  overflow-y: auto;
}

.lib-search-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: 10px;
  cursor: pointer;
}

.lib-search-result:hover {
  background: #eef2ff;
}

.lib-search-thumb {
  width: 40px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: #e2e8f0;
}

.lib-search-thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.lib-search-rmeta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.lib-search-rtitle {
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.lib-search-rsub {
  font-size: 0.78rem;
  color: #64748b;
}

.lib-search-play {
  color: #6366f1;
  font-size: 0.85rem;
}

.lib-search-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.lib-search-section {
  margin: 0.35rem 0.5rem 0.2rem;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.lib-search-empty {
  margin: 0.5rem;
  font-size: 0.85rem;
  color: #64748b;
}

.lib-search-result--ext:hover {
  background: #fffbeb;
}

.lib-search-ext-badge {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #b45309;
  background: #fef3c7;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.lib-search-noresult {
  position: absolute;
  top: calc(100% + 0.4rem);
  left: 0;
  right: 0;
  margin: 0;
  padding: 0.9rem 1rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  color: #64748b;
  font-size: 0.9rem;
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.12);
}

/* --- Hero --- */
.lib-hero {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: linear-gradient(135deg, #1e1b4b, #4338ca);
  background-size: cover;
  background-position: center;
  min-height: 260px;
  display: flex;
}

.lib-hero-close {
  position: absolute;
  top: 0.75rem;
  right: 0.85rem;
  z-index: 2;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  background: rgba(15, 23, 42, 0.45);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
}

.lib-hero-close:hover {
  background: rgba(15, 23, 42, 0.7);
}

/* Animation douce d'apparition/disparition du hero (évite le décalage brusque). */
.lib-hero-anim-enter-active,
.lib-hero-anim-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease, max-height 0.35s ease;
  overflow: hidden;
  max-height: 600px;
}

.lib-hero-anim-enter-from,
.lib-hero-anim-leave-to {
  opacity: 0;
  transform: translateY(-10px);
  max-height: 0;
}

.lib-hero-inner {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.75rem;
  width: 100%;
}

.lib-hero-poster {
  width: 132px;
  height: 198px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
  flex-shrink: 0;
}

.lib-hero-text {
  color: #f8fafc;
  min-width: 0;
}

.lib-hero-title {
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 0.5rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.lib-hero-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0 0 0.75rem;
  color: #e2e8f0;
  font-size: 0.9rem;
}

.lib-pill {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.lib-hero-overview {
  max-width: 60ch;
  margin: 0 0 1rem;
  color: #e2e8f0;
  font-size: 0.92rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.lib-hero-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.lib-btn-play {
  background: #fff;
  color: #1e1b4b;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  padding: 0.65rem 1.5rem;
  font-size: 0.95rem;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.lib-btn-play:hover {
  transform: scale(1.04);
}

.lib-btn-ghost {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 10px;
  padding: 0.65rem 1.25rem;
  font-size: 0.95rem;
  cursor: pointer;
}

.lib-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.25);
}

.lib-hero-empty {
  color: #f8fafc;
}

.lib-hero-empty p {
  margin: 0.4rem 0 0;
  color: #e0e7ff;
}

/* --- Onglets --- */
.lib-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.55rem 0.7rem;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.lib-toolbar-actions {
  display: flex;
  gap: 0.5rem;
}

.lib-add-btn {
  border: none;
  background: linear-gradient(135deg, #4f46e5, #6366f1);
  color: #fff;
  border-radius: 10px;
  padding: 0.6rem 1.1rem;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
  transition: transform 0.15s ease;
}

.lib-add-btn:hover {
  transform: translateY(-1px);
}

.lib-series-eps {
  position: absolute;
  bottom: 0.4rem;
  right: 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.78);
  color: #fff;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.lib-tabs {
  display: flex;
  gap: 0.4rem;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 12px;
}

.lib-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.55rem 1.3rem;
  border-radius: 9px;
  border: none;
  background: transparent;
  color: #475569;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.lib-tab--active {
  background: #fff;
  color: #1e1b4b;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
}

.lib-tab-count {
  font-size: 0.75rem;
  background: rgba(99, 102, 241, 0.15);
  color: #4f46e5;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
}

.lib-tab--active .lib-tab-count {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

.lib-state {
  color: #64748b;
}

.lib-state--error {
  color: #dc2626;
}

/* --- Grille d'affiches --- */
.lib-poster-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--poster-min, 140px), 1fr));
  gap: 1.1rem;
}

.lib-poster-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.lib-poster-img-wrap {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 12px;
  overflow: hidden;
  background: #e2e8f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.lib-poster-card:hover .lib-poster-img-wrap {
  transform: translateY(-4px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.22);
}

.lib-poster-card--active .lib-poster-img-wrap {
  outline: 3px solid #6366f1;
  outline-offset: 2px;
}

.lib-poster-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.lib-poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0.75rem;
  background: linear-gradient(135deg, #334155, #1e293b);
  color: #e2e8f0;
  font-weight: 600;
  font-size: 0.85rem;
}

.lib-poster-hover {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: #fff;
  background: rgba(15, 23, 42, 0.4);
  opacity: 0;
  transition: opacity 0.15s ease;
}

.lib-poster-card:hover .lib-poster-hover {
  opacity: 1;
}

.lib-poster-caption {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* --- Séries --- */
.lib-series-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.25rem;
}

.lib-series-add {
  border: 1px solid #c7d2fe;
  background: #eef2ff;
  color: #4338ca;
  border-radius: 10px;
  padding: 0.55rem 1rem;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
}

.lib-series-add:hover {
  background: #e0e7ff;
}

.lib-series-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: 1rem;
  align-items: start;
}

.lib-series-tile {
  border-radius: 14px;
  border: 1px solid #c7d2fe;
  background: #fff;
  box-shadow: 0 4px 18px rgba(99, 102, 241, 0.08);
  overflow: hidden;
}

.lib-series-tile > summary {
  list-style: none;
  cursor: pointer;
}

.lib-series-tile > summary::-webkit-details-marker {
  display: none;
}

.lib-series-summary {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.85rem 1.15rem;
  font-weight: 600;
  color: #312e81;
}

.lib-series-poster {
  width: 44px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
  background: #e0e7ff;
}

.lib-series-poster--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}

.lib-series-summary .lib-series-title {
  flex: 1;
  min-width: 0;
}

.lib-series-hint {
  flex-shrink: 0;
  color: #94a3b8;
  font-size: 1.1rem;
  line-height: 1;
  letter-spacing: 0.1em;
}

.lib-series-count {
  font-size: 0.75rem;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
}

.lib-series-stack {
  padding: 0 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-top: 1px solid #eef2ff;
}

.lib-season-title {
  margin: 0.75rem 0 0.5rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6366f1;
}

.lib-episode-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.lib-episode-btn {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  text-align: left;
  padding: 0.6rem 0.7rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #1e293b;
  font-size: 0.9rem;
  cursor: pointer;
}

.lib-episode-btn:hover {
  border-color: #c7d2fe;
  background: #fafaff;
}

.lib-episode-btn--active {
  border-color: #818cf8;
  background: #eef2ff;
}

.lib-episode-id {
  font-family: ui-monospace, monospace;
  font-size: 0.72rem;
  color: #64748b;
}
</style>
