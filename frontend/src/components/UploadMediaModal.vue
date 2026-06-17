<template>
  <div class="upload-backdrop" role="dialog" aria-modal="true">
    <div class="upload-modal">
      <div class="upload-header">
        <h2 class="text-lg font-semibold text-slate-900">Ajouter un média</h2>
        <button type="button" class="btn-outline" @click="emitClose" :disabled="uploading">Fermer</button>
      </div>

      <form class="upload-form" @submit.prevent="upload">
        <label>
          Fichier vidéo
          <input type="file" accept="video/*" @change="onFileChange" :disabled="uploading" />
        </label>

        <label>
          Type
          <select v-model="form.mediaType" :disabled="uploading">
            <option value="movie">Film</option>
            <option value="episode">Série (épisode)</option>
          </select>
        </label>

        <!-- Titre proposé automatiquement (modifiable, optionnel) -->
        <label>
          Titre
          <input
            v-model="form.title"
            type="text"
            :placeholder="suggestedTitle || 'Nom du fichier par défaut'"
            :disabled="uploading"
          />
          <span class="upload-hint">
            Laissé vide, le nom du fichier sera utilisé{{ suggestedTitle ? ` (« ${suggestedTitle} »)` : "" }}.
          </span>
        </label>

        <!-- Suggestion d'association Overseerr (films) -->
        <div v-if="form.mediaType === 'movie'" class="upload-assoc">
          <div v-if="association" class="upload-assoc-chosen">
            <img v-if="association.poster_url" :src="association.poster_url" class="upload-assoc-poster" alt="" />
            <div class="upload-assoc-meta">
              <strong>{{ association.title }}</strong>
              <span v-if="association.year">{{ association.year }}</span>
            </div>
            <button type="button" class="ghost" @click="association = null" :disabled="uploading">Retirer</button>
          </div>
          <button
            v-else
            type="button"
            class="ghost upload-assoc-btn"
            @click="openAssoc"
            :disabled="uploading"
          >
            🔗 Associer via Overseerr (affiche, synopsis…)
          </button>
        </div>

        <label>
          Dossier de base (optionnel si MEDIA_FOLDER configuré)
          <input v-model="form.libraryPath" type="text" placeholder="/media/" :disabled="uploading" />
        </label>

        <div v-if="form.mediaType === 'episode'" class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <label>
            Nom de la série
            <input v-model="form.seriesName" type="text" :disabled="uploading" />
          </label>
          <label>
            Numéro de saison
            <input v-model.number="form.seasonNumber" type="number" min="0" :disabled="uploading" />
          </label>
        </div>

        <div v-if="uploading" class="mt-4">
          <div class="mb-2 text-sm text-slate-600">Progression: {{ Math.round(progress) }}%</div>
          <div class="h-2 w-full overflow-hidden rounded bg-slate-200">
            <div class="h-full bg-indigo-600" :style="{ width: `${progress}%` }" />
          </div>
        </div>

        <p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p>

        <div class="upload-actions">
          <button type="submit" class="btn-primary" :disabled="uploading || !form.file">
            {{ uploading ? "Upload en cours..." : "Lancer l'upload" }}
          </button>
          <button type="button" class="btn-outline" :disabled="uploading" @click="emitClose">Annuler</button>
        </div>
      </form>
    </div>

    <AssociationModal
      v-if="showAssoc"
      :initial-query="form.title || suggestedTitle"
      media-type="movie"
      @close="showAssoc = false"
      @associated="onAssociated"
    />
  </div>
</template>

<script>
import { API_BASE } from "../config.js";
import AssociationModal from "./AssociationModal.vue";

function filenameToTitle(filename) {
  const stem = (filename || "").replace(/\.[^/.]+$/, "");
  return stem.replace(/[._]/g, " ").replace(/\s+/g, " ").trim();
}

export default {
  // Upload ergonomique : titre auto depuis le nom de fichier + association Overseerr.
  name: "UploadMediaModal",
  components: { AssociationModal },
  props: {
    token: { type: String, required: true },
    defaultLibraryPath: { type: String, default: "" },
  },
  emits: ["close", "uploaded"],
  data() {
    return {
      form: {
        file: null,
        mediaType: "movie",
        title: "",
        libraryPath: this.defaultLibraryPath,
        seriesName: "",
        seasonNumber: 1,
      },
      suggestedTitle: "",
      association: null, // metadata Overseerr choisie (optionnelle)
      showAssoc: false,
      uploading: false,
      progress: 0,
      error: "",
    };
  },
  methods: {
    emitClose() {
      this.$emit("close");
    },
    onFileChange(event) {
      const f = event?.target?.files?.[0];
      this.form.file = f || null;
      if (f) {
        this.suggestedTitle = filenameToTitle(f.name);
        // Pré-remplit le titre s'il est vide (l'utilisateur peut écraser).
        if (!this.form.title.trim()) this.form.title = this.suggestedTitle;
      }
    },
    openAssoc() {
      this.showAssoc = true;
    },
    onAssociated({ metadata, matchTitle, applyTitle }) {
      this.association = { ...metadata, title: matchTitle };
      if (applyTitle && matchTitle) this.form.title = matchTitle;
      this.showAssoc = false;
    },
    upload() {
      this.error = "";
      if (!this.form.file) {
        this.error = "Sélectionnez un fichier vidéo.";
        return;
      }
      if (!this.token) {
        this.error = "Session invalide (token manquant).";
        return;
      }
      if (this.form.mediaType === "episode") {
        if (!this.form.seriesName || !this.form.seriesName.trim()) {
          this.error = "Nom de la série requis pour une série.";
          return;
        }
        if (this.form.seasonNumber === null || this.form.seasonNumber === undefined) {
          this.error = "Numéro de saison requis pour une série.";
          return;
        }
      }

      const fd = new FormData();
      fd.append("file", this.form.file);
      fd.append("media_type", this.form.mediaType);
      if (this.form.libraryPath && this.form.libraryPath.trim()) {
        fd.append("library_path", this.form.libraryPath.trim());
      }
      if (this.form.mediaType === "episode") {
        fd.append("series_name", this.form.seriesName.trim());
        fd.append("season_number", String(this.form.seasonNumber));
      }

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
          // Post-traitement : titre personnalisé et/ou association (PATCH).
          await this.applyPostUpload(data.id);
          this.uploading = false;
          this.$emit("uploaded", data);
          this.emitClose();
          return;
        }
        this.uploading = false;
        let detail = `Upload échoué (HTTP ${xhr.status})`;
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
        this.error = "Erreur réseau pendant l'upload.";
      };
      xhr.send(fd);
    },
    async applyPostUpload(contentId) {
      if (!contentId) return;
      const patch = {};
      const customTitle = this.form.title.trim();
      // On n'écrase le titre (films) que s'il diffère du défaut serveur.
      if (this.form.mediaType === "movie" && customTitle && customTitle !== this.suggestedTitle) {
        patch.title = customTitle;
      }
      if (this.association) {
        patch.tmdb_id = this.association.tmdb_id || "";
        patch.media_type = this.association.media_type || "";
        patch.poster_url = this.association.poster_url || "";
        patch.backdrop_url = this.association.backdrop_url || "";
        patch.overview = this.association.overview || "";
        patch.year = this.association.year || "";
        if (this.form.mediaType === "movie" && this.association.title) {
          patch.title = customTitle || this.association.title;
        }
      }
      if (Object.keys(patch).length === 0) return;
      try {
        await fetch(`${API_BASE}/contents/${encodeURIComponent(contentId)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
          body: JSON.stringify(patch),
        });
      } catch (e) {
        /* l'upload a réussi ; l'enrichissement est best-effort */
      }
    },
  },
};
</script>

<style scoped>
.upload-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 50;
}

.upload-modal {
  width: 100%;
  max-width: 640px;
  max-height: 90vh;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e3e7f1;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.22);
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.upload-form {
  display: grid;
  gap: 12px;
}

.upload-hint {
  font-size: 0.78rem;
  color: #94a3b8;
}

.upload-assoc {
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  padding: 0.6rem;
  background: #f8fafc;
}

.upload-assoc-btn {
  width: 100%;
}

.upload-assoc-chosen {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.upload-assoc-poster {
  width: 40px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
}

.upload-assoc-meta {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.upload-assoc-meta span {
  font-size: 0.8rem;
  color: #64748b;
}

.upload-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 6px;
}
</style>
