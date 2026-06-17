<template>
  <section class="card server-search-panel">
    <h2>Recherche de fichiers &amp; découverte</h2>
    <p class="text-sm text-slate-600">
      Recherche récursive sur le disque du serveur et découverte de contenus via Overseerr
      (TMDb&nbsp;/&nbsp;TVmaze).
    </p>

    <!-- Onglets -->
    <div class="ssp-tabs" role="tablist">
      <button
        type="button"
        class="ssp-tab"
        :class="{ 'ssp-tab--active': tab === 'disk' }"
        @click="tab = 'disk'"
      >
        💽 Disque serveur
      </button>
      <button
        type="button"
        class="ssp-tab"
        :class="{ 'ssp-tab--active': tab === 'external' }"
        @click="tab = 'external'"
      >
        🌐 Overseerr / TMDb
      </button>
    </div>

    <!-- Recherche disque -->
    <div v-if="tab === 'disk'" class="ssp-body">
      <form class="ssp-searchbar" @submit.prevent="runDiskSearch">
        <input
          v-model="diskQuery"
          type="search"
          placeholder="Nom de fichier ou de dossier (ex. « interstellar »)…"
          aria-label="Recherche disque"
        />
        <button type="submit" class="btn-primary" :disabled="diskLoading">
          {{ diskLoading ? "Recherche…" : "Rechercher" }}
        </button>
      </form>
      <p v-if="diskError" class="text-sm text-red-600">{{ diskError }}</p>
      <p v-else-if="diskDone" class="text-sm text-slate-500">
        {{ diskResults.length }} fichier(s){{ diskTruncated ? " (liste tronquée)" : "" }}.
      </p>
      <ul v-if="diskResults.length" class="ssp-results">
        <li v-for="f in diskResults" :key="f.path" class="ssp-result-row">
          <div class="ssp-result-main">
            <span class="ssp-result-name">{{ f.name }}</span>
            <span class="ssp-result-meta">{{ f.relative_path }}</span>
          </div>
          <div class="ssp-result-side">
            <span class="ssp-badge">{{ f.extension }}</span>
            <span v-if="f.size_bytes != null" class="ssp-size">{{ humanSize(f.size_bytes) }}</span>
            <button type="button" class="ghost ssp-copy" @click="copy(f.path)">Copier le chemin</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Recherche externe Overseerr -->
    <div v-else class="ssp-body">
      <details class="ssp-config" :open="!overseerrConfigured">
        <summary>Configuration Overseerr {{ overseerrConfigured ? "✓" : "(non configurée)" }}</summary>
        <form class="ssp-config-form" @submit.prevent="saveOverseerr">
          <label>
            URL de l'instance Overseerr
            <input v-model="overseerrForm.url" type="url" placeholder="https://overseerr.mondomaine.net" />
          </label>
          <label>
            Clé API (X-Api-Key)
            <input
              v-model="overseerrForm.apiKey"
              type="password"
              :placeholder="overseerrConfigured ? '•••••• (laisser vide pour conserver)' : 'Clé API'"
            />
          </label>
          <button type="submit" class="btn-primary" :disabled="overseerrSaving">
            {{ overseerrSaving ? "Enregistrement…" : "Enregistrer" }}
          </button>
          <p v-if="overseerrMsg" class="text-sm text-emerald-700">{{ overseerrMsg }}</p>
        </form>
      </details>

      <form class="ssp-searchbar" @submit.prevent="runExternalSearch">
        <input
          v-model="extQuery"
          type="search"
          placeholder="Titre d'un film ou d'une série à découvrir…"
          aria-label="Recherche externe"
        />
        <button type="submit" class="btn-primary" :disabled="extLoading">
          {{ extLoading ? "Recherche…" : "Rechercher" }}
        </button>
      </form>
      <p v-if="extError" class="text-sm text-red-600">{{ extError }}</p>
      <p v-else-if="extDone" class="text-sm text-slate-500">
        {{ extResults.length }} résultat(s) sur {{ extTotal }}.
      </p>
      <div v-if="extResults.length" class="ssp-ext-grid">
        <article v-for="r in extResults" :key="r.media_type + '-' + r.id" class="ssp-ext-card">
          <img v-if="r.poster_url" :src="r.poster_url" :alt="r.title" class="ssp-poster" loading="lazy" />
          <div v-else class="ssp-poster ssp-poster--empty">Pas d'affiche</div>
          <div class="ssp-ext-info">
            <h4>{{ r.title }}</h4>
            <p class="ssp-ext-sub">
              <span class="ssp-badge">{{ r.media_type === "tv" ? "Série" : "Film" }}</span>
              <span v-if="r.year">{{ r.year }}</span>
              <span v-if="r.vote_average">★ {{ Number(r.vote_average).toFixed(1) }}</span>
            </p>
            <p class="ssp-ext-overview">{{ r.overview || "Pas de synopsis." }}</p>
          </div>
        </article>
      </div>
      <p class="ssp-attribution">Métadonnées et affiches fournies par TMDb via Overseerr.</p>
    </div>
  </section>
</template>

<script>
import { API_BASE } from "../config.js";

export default {
  name: "ServerSearchPanel",
  inject: ["dashboardApp"],
  data() {
    return {
      tab: "disk",
      // Disque
      diskQuery: "",
      diskResults: [],
      diskLoading: false,
      diskError: "",
      diskDone: false,
      diskTruncated: false,
      // Externe
      extQuery: "",
      extResults: [],
      extTotal: 0,
      extLoading: false,
      extError: "",
      extDone: false,
      // Config Overseerr
      overseerrForm: { url: "", apiKey: "" },
      overseerrConfigured: false,
      overseerrSaving: false,
      overseerrMsg: "",
    };
  },
  computed: {
    token() {
      return this.dashboardApp?.token || "";
    },
  },
  async mounted() {
    await this.loadOverseerrConfig();
  },
  methods: {
    authHeaders() {
      return { Authorization: `Bearer ${this.token}` };
    },
    humanSize(bytes) {
      if (bytes == null) return "";
      const units = ["o", "Ko", "Mo", "Go", "To"];
      let v = bytes;
      let i = 0;
      while (v >= 1024 && i < units.length - 1) {
        v /= 1024;
        i += 1;
      }
      return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
    },
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
      } catch (e) {
        /* no-op */
      }
    },
    async runDiskSearch() {
      this.diskLoading = true;
      this.diskError = "";
      this.diskDone = false;
      try {
        const url = `${API_BASE}/api/search/disk?q=${encodeURIComponent(this.diskQuery.trim())}&limit=200`;
        const res = await fetch(url, { headers: this.authHeaders() });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.diskError = data.detail || `Erreur ${res.status}`;
          this.diskResults = [];
          return;
        }
        this.diskResults = Array.isArray(data.items) ? data.items : [];
        this.diskTruncated = Boolean(data.truncated);
        this.diskDone = true;
      } catch (e) {
        this.diskError = "Impossible de joindre le serveur.";
      } finally {
        this.diskLoading = false;
      }
    },
    async loadOverseerrConfig() {
      try {
        const res = await fetch(`${API_BASE}/api/settings`, { headers: this.authHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        this.overseerrForm.url = data.overseerr_url || "";
        this.overseerrConfigured = Boolean(data.overseerr_api_key_set) && Boolean(data.overseerr_url);
      } catch (e) {
        /* no-op */
      }
    },
    async saveOverseerr() {
      this.overseerrSaving = true;
      this.overseerrMsg = "";
      try {
        const body = { overseerr_url: this.overseerrForm.url.trim() };
        // Clé vide = conserver l'existante (le backend ne l'efface pas par omission).
        if (this.overseerrForm.apiKey.trim()) {
          body.overseerr_api_key = this.overseerrForm.apiKey.trim();
        }
        const res = await fetch(`${API_BASE}/api/settings`, {
          method: "PUT",
          headers: { "Content-Type": "application/json", ...this.authHeaders() },
          body: JSON.stringify(body),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.overseerrMsg = data.detail || `Erreur ${res.status}`;
          return;
        }
        this.overseerrForm.apiKey = "";
        this.overseerrConfigured = Boolean(data.overseerr_api_key_set) && Boolean(data.overseerr_url);
        this.overseerrMsg = "Configuration enregistrée.";
      } catch (e) {
        this.overseerrMsg = "Erreur réseau.";
      } finally {
        this.overseerrSaving = false;
      }
    },
    async runExternalSearch() {
      const q = this.extQuery.trim();
      if (!q) return;
      this.extLoading = true;
      this.extError = "";
      this.extDone = false;
      try {
        const url = `${API_BASE}/api/search/external?q=${encodeURIComponent(q)}`;
        const res = await fetch(url, { headers: this.authHeaders() });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.extError = data.detail || `Erreur ${res.status}`;
          this.extResults = [];
          return;
        }
        this.extResults = Array.isArray(data.items) ? data.items : [];
        this.extTotal = data.total_results || this.extResults.length;
        this.extDone = true;
      } catch (e) {
        this.extError = "Impossible de joindre le serveur.";
      } finally {
        this.extLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.ssp-tabs {
  display: flex;
  gap: 0.5rem;
  margin: 0.75rem 0 1rem;
}

.ssp-tab {
  padding: 0.5rem 1rem;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.ssp-tab--active {
  border-color: #a5b4fc;
  background: linear-gradient(135deg, #eef2ff, #f5f3ff);
  color: #1e1b4b;
}

.ssp-searchbar {
  display: flex;
  gap: 0.6rem;
  margin-bottom: 0.85rem;
}

.ssp-searchbar input {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border-radius: 10px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
}

.ssp-results {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 22rem;
  overflow-y: auto;
}

.ssp-result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.55rem 0.7rem;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}

.ssp-result-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ssp-result-name {
  font-weight: 600;
  color: #1e293b;
}

.ssp-result-meta {
  font-size: 0.78rem;
  color: #64748b;
  word-break: break-all;
}

.ssp-result-side {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.ssp-badge {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #6366f1;
  background: rgba(99, 102, 241, 0.1);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}

.ssp-size {
  font-size: 0.78rem;
  color: #64748b;
}

.ssp-copy {
  font-size: 0.78rem;
  padding: 0.3rem 0.6rem;
}

.ssp-config {
  margin-bottom: 1rem;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
  background: #f8fafc;
}

.ssp-config summary {
  cursor: pointer;
  font-weight: 600;
  color: #334155;
}

.ssp-config-form {
  display: grid;
  gap: 0.6rem;
  margin-top: 0.75rem;
}

.ssp-ext-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr));
  gap: 0.85rem;
}

.ssp-ext-card {
  display: flex;
  gap: 0.7rem;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.6rem;
  background: #fff;
}

.ssp-poster {
  width: 72px;
  height: 108px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
  background: #f1f5f9;
}

.ssp-poster--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  color: #94a3b8;
  text-align: center;
}

.ssp-ext-info {
  min-width: 0;
}

.ssp-ext-info h4 {
  margin: 0 0 0.25rem;
  font-size: 0.98rem;
  color: #1e293b;
}

.ssp-ext-sub {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #64748b;
  margin: 0 0 0.35rem;
}

.ssp-ext-overview {
  margin: 0;
  font-size: 0.82rem;
  color: #475569;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ssp-attribution {
  margin-top: 0.9rem;
  font-size: 0.72rem;
  color: #94a3b8;
}
</style>
