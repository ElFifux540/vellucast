<template>
  <div class="assoc-backdrop" role="dialog" aria-modal="true" @mousedown.self="$emit('close')">
    <div class="assoc-modal">
      <div class="assoc-header">
        <h2>Associer via Overseerr</h2>
        <button type="button" class="ghost" @click="$emit('close')">Fermer</button>
      </div>

      <form class="assoc-search" @submit.prevent="search">
        <input
          ref="input"
          v-model="query"
          type="search"
          placeholder="Titre du film ou de la série…"
          aria-label="Recherche Overseerr"
        />
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? "Recherche…" : "Rechercher" }}
        </button>
      </form>

      <p v-if="error" class="assoc-error">{{ error }}</p>
      <p v-else-if="done && !results.length" class="assoc-hint">Aucun résultat.</p>

      <div v-if="results.length" class="assoc-results">
        <button
          v-for="r in results"
          :key="r.media_type + '-' + r.id"
          type="button"
          class="assoc-card"
          :class="{ 'assoc-card--active': selected && selected.id === r.id && selected.media_type === r.media_type }"
          @click="selected = r"
        >
          <img v-if="r.poster_url" :src="r.poster_url" :alt="r.title" class="assoc-poster" loading="lazy" />
          <div v-else class="assoc-poster assoc-poster--empty">—</div>
          <div class="assoc-info">
            <h4>{{ r.title }}</h4>
            <p class="assoc-sub">
              <span class="assoc-badge">{{ r.media_type === "tv" ? "Série" : "Film" }}</span>
              <span v-if="r.year">{{ r.year }}</span>
              <span v-if="r.vote_average">★ {{ Number(r.vote_average).toFixed(1) }}</span>
            </p>
            <p class="assoc-overview">{{ r.overview || "Pas de synopsis." }}</p>
          </div>
        </button>
      </div>

      <div class="assoc-footer">
        <label v-if="selected" class="assoc-titlecheck">
          <input v-model="applyTitle" type="checkbox" />
          Mettre à jour le titre avec « {{ selected.title }} »
        </label>
        <div class="assoc-actions">
          <button type="button" class="ghost" @click="$emit('close')">Annuler</button>
          <button type="button" class="btn-primary" :disabled="!selected" @click="confirm">
            Associer
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

export default {
  name: "AssociationModal",
  inject: ["dashboardApp"],
  props: {
    initialQuery: { type: String, default: "" },
    // Filtre le type proposé : "movie", "tv" ou "" (tous).
    mediaType: { type: String, default: "" },
  },
  emits: ["close", "associated"],
  data() {
    return {
      query: this.initialQuery,
      results: [],
      selected: null,
      loading: false,
      error: "",
      done: false,
      applyTitle: true,
    };
  },
  computed: {
    token() {
      return this.dashboardApp?.token || "";
    },
  },
  mounted() {
    this.$nextTick(() => this.$refs.input?.focus());
    if (this.query.trim()) this.search();
  },
  methods: {
    async search() {
      const q = this.query.trim();
      if (!q) return;
      this.loading = true;
      this.error = "";
      this.done = false;
      try {
        const res = await fetch(`${API_BASE}/api/search/external?q=${encodeURIComponent(q)}`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.error = data.detail || `Erreur ${res.status}`;
          this.results = [];
          return;
        }
        let items = Array.isArray(data.items) ? data.items : [];
        // Ne proposer que le bon type (films pour un film, séries pour une série).
        if (this.mediaType) items = items.filter((r) => r.media_type === this.mediaType);
        this.results = items;
        this.done = true;
      } catch (e) {
        this.error = "Impossible de joindre le serveur.";
      } finally {
        this.loading = false;
      }
    },
    confirm() {
      if (!this.selected) return;
      const r = this.selected;
      // Métadonnées normalisées prêtes pour un PATCH /contents/{id}.
      const metadata = {
        tmdb_id: r.tmdb_id != null ? String(r.tmdb_id) : "",
        media_type: r.media_type || "",
        poster_url: r.poster_url || "",
        backdrop_url: r.backdrop_url || "",
        overview: r.overview || "",
        year: r.year != null ? String(r.year) : "",
      };
      this.$emit("associated", {
        metadata,
        matchTitle: r.title,
        applyTitle: this.applyTitle,
      });
    },
  },
};
</script>

<style scoped>
.assoc-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 400;
}

.assoc-modal {
  width: 100%;
  max-width: 720px;
  max-height: 86vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.3);
}

.assoc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.assoc-header h2 {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
}

.assoc-search {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.85rem;
}

.assoc-search input {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
}

.assoc-error {
  color: #dc2626;
  font-size: 0.85rem;
}

.assoc-hint {
  color: #64748b;
  font-size: 0.85rem;
}

.assoc-results {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.2rem;
}

.assoc-card {
  display: flex;
  gap: 0.7rem;
  text-align: left;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.6rem;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.assoc-card:hover {
  border-color: #c7d2fe;
}

.assoc-card--active {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
}

.assoc-poster {
  width: 64px;
  height: 96px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
  background: #f1f5f9;
}

.assoc-poster--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
}

.assoc-info {
  min-width: 0;
}

.assoc-info h4 {
  margin: 0 0 0.25rem;
  font-size: 0.98rem;
  color: #1e293b;
}

.assoc-sub {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #64748b;
  margin: 0 0 0.35rem;
}

.assoc-badge {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
}

.assoc-overview {
  margin: 0;
  font-size: 0.8rem;
  color: #475569;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.assoc-footer {
  margin-top: 0.9rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.assoc-titlecheck {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: #475569;
}

.assoc-actions {
  display: flex;
  gap: 0.6rem;
  margin-left: auto;
}
</style>
