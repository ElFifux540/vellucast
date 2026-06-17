<template>
  <div class="info-backdrop" role="dialog" aria-modal="true" @mousedown.self="$emit('close')">
    <div class="info-modal">
      <!-- Bannière -->
      <div
        class="info-hero"
        :style="heroStyle"
      >
        <button type="button" class="info-close" @click="$emit('close')">✕</button>
        <div class="info-hero-overlay">
          <div class="info-hero-content">
            <img v-if="content.poster_url" :src="content.poster_url" :alt="content.title" class="info-poster" />
            <div class="info-hero-text">
              <h2>{{ content.title }}</h2>
              <p class="info-meta">
                <span v-if="content.year">{{ content.year }}</span>
                <span v-if="content.media_type" class="info-badge">
                  {{ content.media_type === "tv" ? "Série" : "Film" }}
                </span>
                <span v-if="content.tmdb_id" class="info-badge">TMDb #{{ content.tmdb_id }}</span>
                <span v-if="content.__external" class="info-badge info-badge--ext">
                  Externe · non disponible localement
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="info-body">
        <p class="info-overview">
          {{ content.overview || "Aucun synopsis. Associez ce média via Overseerr pour l'enrichir." }}
        </p>
        <p v-if="content.media_path" class="info-path"><span>Fichier</span> {{ content.media_path }}</p>

        <!-- Édition (admin) — masquée pour un résultat externe (aucun fichier en base) -->
        <div v-if="isAdmin && !content.__external" class="info-edit">
          <h3>Modifier</h3>
          <label>
            Titre
            <input v-model="form.title" type="text" />
          </label>
          <label>
            URL de la bannière (backdrop)
            <input v-model="form.backdrop_url" type="url" placeholder="https://…" />
          </label>
          <label>
            URL de l'affiche (poster)
            <input v-model="form.poster_url" type="url" placeholder="https://…" />
          </label>

          <p v-if="message" class="info-msg">{{ message }}</p>

          <div class="info-actions">
            <button type="button" class="ghost" @click="$emit('associate')">
              🔗 Corriger l'association (Overseerr)
            </button>
            <button type="button" class="btn-primary" :disabled="saving" @click="save">
              {{ saving ? "Enregistrement…" : "Enregistrer" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

export default {
  // Modale infos média (bannière, affiche, synopsis) + édition admin.
  name: "MediaInfoModal",
  inject: ["dashboardApp"],
  props: {
    content: { type: Object, required: true },
    isAdmin: { type: Boolean, default: false },
  },
  emits: ["close", "associate", "updated"],
  data() {
    return {
      form: {
        title: this.content.title || "",
        backdrop_url: this.content.backdrop_url || "",
        poster_url: this.content.poster_url || "",
      },
      saving: false,
      message: "",
    };
  },
  computed: {
    token() {
      return this.dashboardApp?.token || "";
    },
    heroStyle() {
      if (this.content.backdrop_url) {
        return {
          backgroundImage: `linear-gradient(to top, rgba(15,23,42,0.95), rgba(15,23,42,0.35)), url("${this.content.backdrop_url}")`,
        };
      }
      return { background: "linear-gradient(135deg, #312e81, #4f46e5)" };
    },
  },
  watch: {
    // Recharge le formulaire si le contenu change (après association).
    content: {
      deep: true,
      handler(c) {
        this.form.title = c.title || "";
        this.form.backdrop_url = c.backdrop_url || "";
        this.form.poster_url = c.poster_url || "";
      },
    },
  },
  methods: {
    async save() {
      this.saving = true;
      this.message = "";
      try {
        const res = await fetch(`${API_BASE}/contents/${encodeURIComponent(this.content.id)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
          body: JSON.stringify({
            title: this.form.title.trim() || this.content.title,
            backdrop_url: this.form.backdrop_url.trim(),
            poster_url: this.form.poster_url.trim(),
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          this.message = data.detail || `Erreur ${res.status}`;
          return;
        }
        this.$emit("updated");
        this.message = "Enregistré.";
      } catch (e) {
        this.message = "Erreur réseau.";
      } finally {
        this.saving = false;
      }
    },
  },
};
</script>

<style scoped>
.info-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 380;
}

.info-modal {
  width: 100%;
  max-width: 760px;
  max-height: 88vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.32);
}

.info-hero {
  position: relative;
  min-height: 220px;
  background-size: cover;
  background-position: center;
}

.info-close {
  position: absolute;
  top: 10px;
  right: 12px;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  border: none;
  background: rgba(15, 23, 42, 0.55);
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  z-index: 3; /* au-dessus de l'overlay du hero, sinon le clic est intercepté */
}

.info-hero-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  padding: 1.25rem;
  pointer-events: none; /* laisse passer le clic vers le bouton de fermeture */
}

.info-hero-content {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.info-poster {
  width: 96px;
  height: 144px;
  object-fit: cover;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
  flex-shrink: 0;
}

.info-hero-text h2 {
  margin: 0 0 0.35rem;
  color: #fff;
  font-size: 1.5rem;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
}

.info-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin: 0;
  color: #e2e8f0;
  font-size: 0.85rem;
}

.info-badge {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
}

.info-badge--ext {
  background: #fef3c7;
  color: #b45309;
}

.info-body {
  padding: 1.25rem;
  overflow-y: auto;
}

.info-overview {
  margin: 0 0 1rem;
  color: #334155;
  line-height: 1.5;
  font-size: 0.92rem;
}

.info-path {
  margin: 0 0 1rem;
  font-size: 0.78rem;
  color: #94a3b8;
  word-break: break-all;
}

.info-path span {
  font-weight: 600;
  color: #64748b;
  margin-right: 0.4rem;
}

.info-edit {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
  display: grid;
  gap: 0.65rem;
}

.info-edit h3 {
  margin: 0;
  font-size: 0.95rem;
  color: #1e293b;
}

.info-edit label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}

.info-edit input {
  padding: 0.55rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.9rem;
}

.info-msg {
  margin: 0;
  font-size: 0.82rem;
  color: #059669;
}

.info-actions {
  display: flex;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  margin-top: 0.3rem;
}
</style>
