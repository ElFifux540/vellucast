<template>
  <div class="ep-backdrop" role="dialog" aria-modal="true" @mousedown.self="emitClose">
    <div class="ep-modal">
      <div class="ep-header">
        <h2>Ajouter un épisode</h2>
        <button type="button" class="ghost" @click="emitClose" :disabled="uploading">Fermer</button>
      </div>

      <p class="ep-series">
        Série : <strong>{{ seriesName }}</strong>
      </p>
      <p class="ep-hint">
        Le fichier sera enregistré au format <code>SxxEyy</code> (saison/épisode) pour être
        automatiquement regroupé avec les autres épisodes de cette série.
      </p>

      <form class="ep-form" @submit.prevent="upload">
        <label>
          Fichier vidéo
          <input type="file" accept="video/*" @change="onFileChange" :disabled="uploading" />
        </label>

        <div class="ep-grid">
          <label>
            Saison (x)
            <input v-model.number="season" type="number" min="1" :disabled="uploading" />
          </label>
          <label>
            Épisode (y)
            <input v-model.number="episode" type="number" min="1" :disabled="uploading" />
          </label>
        </div>

        <p class="ep-preview">
          Titre généré : <strong>{{ generatedTitle }}</strong>
        </p>

        <div v-if="uploading" class="ep-progress">
          <div class="ep-progress-label">Progression : {{ Math.round(progress) }}%</div>
          <div class="ep-progress-bar"><div :style="{ width: progress + '%' }" /></div>
        </div>

        <p v-if="error" class="ep-error">{{ error }}</p>

        <div class="ep-actions">
          <button type="submit" class="btn-primary" :disabled="uploading || !file">
            {{ uploading ? "Envoi…" : "Ajouter l'épisode" }}
          </button>
          <button type="button" class="ghost" :disabled="uploading" @click="emitClose">Annuler</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

function pad2(n) {
  return String(Math.max(0, parseInt(n, 10) || 0)).padStart(2, "0");
}

export default {
  name: "AddEpisodeModal",
  inject: ["dashboardApp"],
  props: {
    seriesName: { type: String, required: true },
    // Métadonnées héritées de la série (poster/backdrop/overview/year/tmdb_id/media_type).
    seriesMetadata: { type: Object, default: () => ({}) },
  },
  emits: ["close", "added"],
  data() {
    return {
      file: null,
      season: 1,
      episode: 1,
      uploading: false,
      progress: 0,
      error: "",
    };
  },
  computed: {
    token() {
      return this.dashboardApp?.token || "";
    },
    generatedTitle() {
      return `${this.seriesName} - S${pad2(this.season)}E${pad2(this.episode)}`;
    },
  },
  methods: {
    emitClose() {
      this.$emit("close");
    },
    onFileChange(e) {
      this.file = e?.target?.files?.[0] || null;
    },
    upload() {
      this.error = "";
      if (!this.file) {
        this.error = "Sélectionnez un fichier vidéo.";
        return;
      }
      if (!this.season || !this.episode) {
        this.error = "Indiquez la saison et l'épisode.";
        return;
      }

      const fd = new FormData();
      fd.append("file", this.file);
      fd.append("media_type", "episode");
      fd.append("series_name", this.seriesName);
      fd.append("season_number", String(this.season));

      this.uploading = true;
      this.progress = 0;

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/api/upload`, true);
      xhr.setRequestHeader("Authorization", `Bearer ${this.token}`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) this.progress = (e.loaded / e.total) * 100;
      };
      xhr.onload = async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          let data = {};
          try {
            data = JSON.parse(xhr.responseText || "{}");
          } catch {
            data = {};
          }
          await this.finalizeEpisode(data.id);
          this.uploading = false;
          this.$emit("added");
          this.emitClose();
          return;
        }
        this.uploading = false;
        let detail = `Échec (HTTP ${xhr.status})`;
        try {
          const body = JSON.parse(xhr.responseText || "{}");
          detail = body?.detail || body?.error || detail;
        } catch {
          /* ignore */
        }
        this.error = detail;
      };
      xhr.onerror = () => {
        this.uploading = false;
        this.error = "Erreur réseau pendant l'envoi.";
      };
      xhr.send(fd);
    },
    async finalizeEpisode(contentId) {
      if (!contentId) return;
      // Titre au format SxxEyy + héritage des métadonnées de la série.
      const patch = { title: this.generatedTitle };
      const m = this.seriesMetadata || {};
      for (const k of ["poster_url", "backdrop_url", "overview", "year", "tmdb_id", "media_type"]) {
        if (m[k]) patch[k] = m[k];
      }
      try {
        await fetch(`${API_BASE}/contents/${encodeURIComponent(contentId)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
          body: JSON.stringify(patch),
        });
      } catch (e) {
        /* l'envoi a réussi ; le nommage est best-effort */
      }
    },
  },
};
</script>

<style scoped>
.ep-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 400;
}

.ep-modal {
  width: 100%;
  max-width: 520px;
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.28);
}

.ep-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.ep-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
}

.ep-series {
  margin: 0 0 0.5rem;
  color: #334155;
}

.ep-hint {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
}

.ep-hint code {
  background: #e2e8f0;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
}

.ep-form {
  display: grid;
  gap: 0.75rem;
}

.ep-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.ep-form label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.88rem;
  color: #334155;
}

.ep-form input {
  padding: 0.55rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.92rem;
}

.ep-preview {
  margin: 0;
  font-size: 0.85rem;
  color: #475569;
}

.ep-progress-bar {
  height: 8px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.ep-progress-bar div {
  height: 100%;
  background: #4f46e5;
}

.ep-progress-label {
  font-size: 0.82rem;
  color: #64748b;
  margin-bottom: 0.3rem;
}

.ep-error {
  margin: 0;
  font-size: 0.85rem;
  color: #dc2626;
}

.ep-actions {
  display: flex;
  gap: 0.6rem;
  margin-top: 0.3rem;
}
</style>
