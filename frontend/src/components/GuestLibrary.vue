<template>
  <div class="gl-root" :style="{ '--poster-min': posterMin }">
    <transition name="gl-fade" mode="out-in">
      <!-- Lecture -->
      <VideoPlayer
        v-if="playing"
        key="player"
        :token="token"
        :content="playing"
        @back="playing = null"
      />

      <!-- Catalogue invité -->
      <div v-else key="catalog" class="gl-catalog">
        <header class="gl-header">
          <div>
            <h1 class="gl-title">Contenus partagés avec vous</h1>
            <p class="gl-sub">{{ contents.length }} élément(s) accessible(s) via ce lien.</p>
          </div>
          <div class="gl-size" role="group" aria-label="Taille des affiches">
            <span class="gl-size-label">Taille</span>
            <button
              v-for="opt in sizeOptions"
              :key="opt.key"
              type="button"
              class="gl-size-btn"
              :class="{ 'gl-size-btn--active': posterSize === opt.key }"
              @click="setSize(opt.key)"
            >
              {{ opt.label }}
            </button>
          </div>
        </header>

        <p v-if="!contents.length" class="gl-empty">Aucun contenu disponible.</p>

        <div v-else class="gl-grid">
          <button
            v-for="c in contents"
            :key="c.id"
            type="button"
            class="gl-card"
            @click="playing = c"
          >
            <div class="gl-poster">
              <img v-if="c.poster_url" :src="c.poster_url" :alt="c.title" loading="lazy" />
              <div v-else class="gl-poster-empty"><span>{{ c.title }}</span></div>
              <span class="gl-play">▶</span>
            </div>
            <span class="gl-caption">{{ c.title }}</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import VideoPlayer from "./VideoPlayer.vue";

const SIZE_MAP = { small: "110px", medium: "150px", large: "200px" };

export default {
  name: "GuestLibrary",
  components: { VideoPlayer },
  props: {
    token: { type: String, required: true },
    contents: { type: Array, default: () => [] },
  },
  data() {
    return {
      playing: null,
      posterSize: "medium",
      sizeOptions: [
        { key: "small", label: "S" },
        { key: "medium", label: "M" },
        { key: "large", label: "L" },
      ],
    };
  },
  computed: {
    posterMin() {
      return SIZE_MAP[this.posterSize] || SIZE_MAP.medium;
    },
  },
  mounted() {
    // Préférence de taille partagée avec le reste du site (persistée par navigateur).
    try {
      const saved = localStorage.getItem("vellucast_poster_size");
      if (saved && SIZE_MAP[saved]) this.posterSize = saved;
    } catch (e) {
      /* no-op */
    }
  },
  methods: {
    setSize(key) {
      this.posterSize = key;
      try {
        localStorage.setItem("vellucast_poster_size", key);
      } catch (e) {
        /* no-op */
      }
    },
  },
};
</script>

<style scoped>
.gl-root {
  width: 100%;
}

.gl-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1.25rem;
}

.gl-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
}

.gl-sub {
  color: #64748b;
  margin: 0.25rem 0 0;
}

.gl-size {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.gl-size-label {
  font-size: 0.8rem;
  color: #64748b;
  margin-right: 0.25rem;
}

.gl-size-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  font-weight: 700;
  font-size: 0.8rem;
  cursor: pointer;
}

.gl-size-btn--active {
  background: #1e1b4b;
  border-color: #1e1b4b;
  color: #fff;
}

.gl-empty {
  color: #64748b;
}

.gl-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--poster-min, 150px), 1fr));
  gap: 1.1rem;
}

.gl-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.gl-poster {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: 12px;
  overflow: hidden;
  background: #e2e8f0;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.gl-card:hover .gl-poster {
  transform: translateY(-4px);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.24);
}

.gl-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gl-poster-empty {
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

.gl-play {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: #fff;
  background: rgba(15, 23, 42, 0.4);
  opacity: 0;
  transition: opacity 0.18s ease;
}

.gl-card:hover .gl-play {
  opacity: 1;
}

.gl-caption {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  line-height: 1.25;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Animation douce entre catalogue et lecteur */
.gl-fade-enter-active,
.gl-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.gl-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.gl-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
