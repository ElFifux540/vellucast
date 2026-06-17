<template>
  <div class="sd-root" :style="{ '--poster-min': posterMin }">
    <!-- Bannière de la série -->
    <section class="sd-hero" :style="heroStyle">
      <button type="button" class="sd-back" @click="goBack">← Retour</button>
      <div class="sd-hero-inner">
        <img v-if="seriesMeta.poster_url" :src="seriesMeta.poster_url" class="sd-hero-poster" alt="" />
        <div class="sd-hero-text">
          <h1 class="sd-hero-title">{{ seriesName }}</h1>
          <p class="sd-hero-meta">
            <span class="sd-pill">Série</span>
            <span>{{ seasons.length }} saison(s)</span>
            <span>{{ episodes.length }} épisode(s)</span>
          </p>
          <p v-if="seriesMeta.overview" class="sd-hero-overview">{{ seriesMeta.overview }}</p>
          <div class="sd-hero-actions">
            <button v-if="isAdmin" type="button" class="sd-btn-ghost" @click="$emit('add-episodes')">
              ➕ Ajouter des épisodes
            </button>
          </div>
        </div>
      </div>
    </section>

    <transition name="sd-fade" mode="out-in">
      <!-- Vue saisons (bannières) -->
      <div v-if="selectedSeason === null" key="seasons" class="sd-seasons">
        <h2 class="sd-section-title">Saisons</h2>
        <div class="sd-season-grid">
          <button
            v-for="s in seasons"
            :key="s.number"
            type="button"
            class="sd-season-card"
            :style="seasonStyle"
            @click="selectedSeason = s.number"
          >
            <span class="sd-season-num">Saison {{ s.number }}</span>
            <span class="sd-season-count">{{ s.count }} épisode(s)</span>
          </button>
        </div>
      </div>

      <!-- Vue épisodes d'une saison (grille façon films) -->
      <div v-else key="episodes" class="sd-episodes">
        <div class="sd-ep-head">
          <button type="button" class="sd-back-light" @click="selectedSeason = null">
            ← Saisons
          </button>
          <h2 class="sd-section-title">Saison {{ selectedSeason }}</h2>
        </div>
        <div class="sd-ep-grid">
          <button
            v-for="ep in episodesForSeason"
            :key="ep.content.id"
            type="button"
            class="sd-ep-card"
            @click="$emit('play', ep.content)"
            @contextmenu.prevent.stop="$emit('context', $event, ep.content)"
          >
            <div class="sd-ep-thumb">
              <img v-if="ep.content.poster_url" :src="ep.content.poster_url" :alt="ep.label" loading="lazy" />
              <div v-else class="sd-ep-thumb-empty">📺</div>
              <span class="sd-ep-badge">E{{ pad2(ep.episode) }}</span>
              <span class="sd-ep-play">▶</span>
            </div>
            <span class="sd-ep-label">{{ ep.label }}</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
function pad2(n) {
  return String(Math.max(0, parseInt(n, 10) || 0)).padStart(2, "0");
}

function parseSE(title) {
  const t = (title || "").trim();
  let m = t.match(/^(.+?)[\s-]+S(\d{1,2})E(\d{1,2})\b[\s-]*(.*)$/i);
  if (m) return { season: +m[2], episode: +m[3], remainder: (m[4] || "").trim() };
  m = t.match(/^(.+?)\s*-\s*Saison\s+(\d+)\s*-\s*(?:Ép\.\s*(\d+)\s*-\s*)?(.+)$/i);
  if (m) return { season: +m[2], episode: m[3] != null ? +m[3] : null, remainder: (m[4] || "").trim() };
  return { season: 1, episode: null, remainder: "" };
}

export default {
  name: "SeriesDetail",
  props: {
    seriesName: { type: String, required: true },
    episodes: { type: Array, default: () => [] },
    seriesMeta: { type: Object, default: () => ({}) },
    posterMin: { type: String, default: "140px" },
    isAdmin: { type: Boolean, default: false },
  },
  emits: ["back", "play", "context", "add-episodes"],
  data() {
    return { selectedSeason: null };
  },
  computed: {
    parsed() {
      return this.episodes.map((c) => ({ content: c, ...parseSE(c.title) }));
    },
    seasons() {
      const map = {};
      for (const e of this.parsed) {
        map[e.season] = (map[e.season] || 0) + 1;
      }
      return Object.keys(map)
        .map(Number)
        .sort((a, b) => a - b)
        .map((number) => ({ number, count: map[number] }));
    },
    episodesForSeason() {
      return this.parsed
        .filter((e) => e.season === this.selectedSeason)
        .sort((a, b) => (a.episode || 0) - (b.episode || 0))
        .map((e) => ({
          ...e,
          label: e.remainder
            ? `Ép. ${e.episode ?? "?"} — ${e.remainder}`
            : `Épisode ${e.episode ?? "?"}`,
        }));
    },
    heroStyle() {
      if (this.seriesMeta.backdrop_url) {
        return {
          backgroundImage: `linear-gradient(to right, rgba(15,23,42,0.92), rgba(15,23,42,0.55)), url("${this.seriesMeta.backdrop_url}")`,
        };
      }
      return {};
    },
    seasonStyle() {
      if (this.seriesMeta.backdrop_url) {
        return {
          backgroundImage: `linear-gradient(rgba(15,23,42,0.55), rgba(15,23,42,0.75)), url("${this.seriesMeta.backdrop_url}")`,
        };
      }
      return {};
    },
  },
  methods: {
    pad2,
    goBack() {
      if (this.selectedSeason !== null) this.selectedSeason = null;
      else this.$emit("back");
    },
  },
};
</script>

<style scoped>
.sd-root {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sd-hero {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: linear-gradient(135deg, #1e1b4b, #4338ca);
  background-size: cover;
  background-position: center;
  min-height: 240px;
}

.sd-back,
.sd-back-light {
  border: none;
  cursor: pointer;
  font-weight: 600;
}

.sd-back {
  position: absolute;
  top: 0.85rem;
  left: 0.95rem;
  z-index: 2;
  background: rgba(15, 23, 42, 0.45);
  color: #fff;
  border-radius: 10px;
  padding: 0.45rem 0.9rem;
}

.sd-back:hover {
  background: rgba(15, 23, 42, 0.7);
}

.sd-hero-inner {
  display: flex;
  gap: 1.5rem;
  align-items: flex-end;
  padding: 1.75rem;
  min-height: 240px;
}

.sd-hero-poster {
  width: 130px;
  height: 195px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
  flex-shrink: 0;
}

.sd-hero-text {
  color: #f8fafc;
  min-width: 0;
}

.sd-hero-title {
  font-size: 2rem;
  font-weight: 800;
  margin: 0 0 0.5rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.sd-hero-meta {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  margin: 0 0 0.75rem;
  color: #e2e8f0;
  font-size: 0.9rem;
}

.sd-pill {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.2);
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.sd-hero-overview {
  max-width: 60ch;
  margin: 0 0 1rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sd-btn-ghost {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 10px;
  padding: 0.55rem 1.1rem;
  font-size: 0.9rem;
  cursor: pointer;
}

.sd-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.25);
}

.sd-section-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.85rem;
}

.sd-season-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.sd-season-card {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 0.25rem;
  aspect-ratio: 16 / 9;
  padding: 1rem;
  border: none;
  border-radius: 14px;
  background-color: #312e81;
  background-size: cover;
  background-position: center;
  color: #fff;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.18);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.sd-season-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.28);
}

.sd-season-num {
  font-size: 1.15rem;
  font-weight: 800;
}

.sd-season-count {
  font-size: 0.82rem;
  opacity: 0.85;
}

.sd-ep-head {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.85rem;
}

.sd-back-light {
  background: #eef2ff;
  color: #4338ca;
  border-radius: 10px;
  padding: 0.45rem 0.9rem;
}

.sd-back-light:hover {
  background: #e0e7ff;
}

.sd-ep-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--poster-min, 140px), 1fr));
  gap: 1.1rem;
}

.sd-ep-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.sd-ep-thumb {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 12px;
  overflow: hidden;
  background: #e2e8f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.sd-ep-card:hover .sd-ep-thumb {
  transform: translateY(-4px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.22);
}

.sd-ep-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.sd-ep-thumb-empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  background: linear-gradient(135deg, #334155, #1e293b);
}

.sd-ep-badge {
  position: absolute;
  top: 0.4rem;
  left: 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(15, 23, 42, 0.75);
  color: #fff;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.sd-ep-play {
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

.sd-ep-card:hover .sd-ep-play {
  opacity: 1;
}

.sd-ep-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sd-fade-enter-active,
.sd-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.sd-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.sd-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
