<template>
  <div class="su-backdrop" role="dialog" aria-modal="true" @mousedown.self="emitClose">
    <div class="su-modal">
      <div class="su-header">
        <h2>{{ presetName ? `Ajouter des épisodes à « ${presetName} »` : "Ajouter une série / des épisodes" }}</h2>
        <button type="button" class="ghost" @click="emitClose" :disabled="busy">Fermer</button>
      </div>

      <!-- Choix de la série : existante ou nouvelle (sauf si imposée par le contexte) -->
      <div v-if="!presetName" class="su-mode">
        <label class="su-radio">
          <input type="radio" value="existing" v-model="mode" :disabled="busy || !existingSeries.length" />
          Série existante
        </label>
        <label class="su-radio">
          <input type="radio" value="new" v-model="mode" :disabled="busy" />
          Nouvelle série
        </label>
      </div>

      <div class="su-series">
        <template v-if="presetName">
          <p class="su-locked">Série : <strong>{{ presetName }}</strong></p>
        </template>
        <template v-else-if="mode === 'existing'">
          <label class="su-field">
            Série
            <select v-model="existingName" :disabled="busy">
              <option value="" disabled>— Choisir une série —</option>
              <option v-for="s in existingSeries" :key="s.name" :value="s.name">{{ s.name }}</option>
            </select>
          </label>
        </template>
        <template v-else>
          <label class="su-field">
            Nom de la nouvelle série
            <input v-model="newName" type="text" placeholder="ex. The 100" :disabled="busy" />
          </label>
          <div class="su-assoc">
            <div v-if="newMeta.poster_url || newMeta.tmdb_id" class="su-assoc-chosen">
              <img v-if="newMeta.poster_url" :src="newMeta.poster_url" class="su-assoc-poster" alt="" />
              <span>Associée{{ newMeta.year ? " (" + newMeta.year + ")" : "" }}</span>
              <button type="button" class="ghost" @click="newMeta = {}" :disabled="busy">Retirer</button>
            </div>
            <button v-else type="button" class="ghost" @click="showAssoc = true" :disabled="busy || !newName.trim()">
              🔗 Associer via Overseerr
            </button>
          </div>
        </template>
      </div>

      <p class="su-hint">
        Sélectionnez un ou plusieurs fichiers : la saison et l'épisode sont détectés
        automatiquement (S01E01, 1x01, E01…) et restent modifiables avant l'ajout.
      </p>

      <label class="su-filebtn">
        <input type="file" accept="video/*" multiple @change="onFilesChange" :disabled="busy" />
        <span>📂 Choisir des fichiers</span>
      </label>

      <div v-if="rows.length" class="su-table">
        <div class="su-row su-row--head">
          <span class="su-col-file">Fichier</span>
          <span class="su-col-num">Saison</span>
          <span class="su-col-num">Épisode</span>
          <span class="su-col-title">Titre généré</span>
          <span class="su-col-state">État</span>
        </div>
        <div v-for="(row, i) in rows" :key="i" class="su-row">
          <span class="su-col-file" :title="row.file.name">{{ row.file.name }}</span>
          <input class="su-col-num" type="number" min="1" v-model.number="row.season" :disabled="busy" />
          <input class="su-col-num" type="number" min="1" v-model.number="row.episode" :disabled="busy" />
          <span class="su-col-title">{{ titleFor(row) }}</span>
          <span class="su-col-state" :class="'su-state--' + row.status">{{ stateLabel(row) }}</span>
        </div>
      </div>

      <p v-if="error" class="su-error">{{ error }}</p>

      <div class="su-actions">
        <button type="button" class="btn-primary" :disabled="busy || !canSubmit" @click="uploadAll">
          {{ busy ? `Envoi ${doneCount}/${rows.length}…` : `Ajouter ${rows.length} épisode(s)` }}
        </button>
        <button type="button" class="ghost" :disabled="busy" @click="emitClose">Annuler</button>
      </div>
    </div>

    <AssociationModal
      v-if="showAssoc"
      :initial-query="newName"
      media-type="tv"
      @close="showAssoc = false"
      @associated="onAssociated"
    />
  </div>
</template>

<script>
import { API_BASE } from "../config.js";
import AssociationModal from "./AssociationModal.vue";

function pad2(n) {
  return String(Math.max(0, parseInt(n, 10) || 0)).padStart(2, "0");
}

function detectSeasonEpisode(name) {
  const n = name.replace(/\.[^/.]+$/, "");
  let m = n.match(/[Ss](\d{1,2})[\s._-]*[Ee](\d{1,2})/);
  if (m) return { season: +m[1], episode: +m[2] };
  m = n.match(/\b(\d{1,2})\s*[xX]\s*(\d{1,2})\b/);
  if (m) return { season: +m[1], episode: +m[2] };
  m = n.match(/[Ss]aison[\s._-]*(\d{1,2}).*?[Ee]p?(?:isode)?[\s._-]*(\d{1,2})/);
  if (m) return { season: +m[1], episode: +m[2] };
  m = n.match(/[Ee]pisode[\s._-]*(\d{1,2})/i);
  if (m) return { season: 1, episode: +m[1] };
  return { season: 1, episode: null };
}

function guessSeriesName(name) {
  const n = name.replace(/\.[^/.]+$/, "");
  const cut = n.split(/[Ss]\d{1,2}[\s._-]*[Ee]\d{1,2}|\b\d{1,2}\s*[xX]\s*\d{1,2}\b/)[0];
  // On retire les séparateurs de fin (« The 100 - » → « The 100 »).
  return (cut || n).replace(/[._]/g, " ").replace(/\s+/g, " ").replace(/[\s\-_]+$/, "").trim();
}

export default {
  name: "SeriesUploadModal",
  components: { AssociationModal },
  inject: ["dashboardApp"],
  props: {
    // Séries déjà enregistrées : [{ name, metadata }]
    existingSeries: { type: Array, default: () => [] },
    // Si défini, on ajoute directement à cette série (depuis le menu contextuel).
    presetName: { type: String, default: "" },
    presetMetadata: { type: Object, default: () => ({}) },
  },
  emits: ["close", "done"],
  data() {
    return {
      mode: this.presetName ? "existing" : this.existingSeries.length ? "existing" : "new",
      existingName: this.presetName || "",
      newName: "",
      newMeta: {},
      rows: [],
      showAssoc: false,
      busy: false,
      error: "",
    };
  },
  computed: {
    token() {
      return this.dashboardApp?.token || "";
    },
    effectiveName() {
      if (this.presetName) return this.presetName;
      return this.mode === "existing" ? this.existingName : this.newName.trim();
    },
    effectiveMeta() {
      if (this.presetName) return this.presetMetadata || {};
      if (this.mode === "existing") {
        const found = this.existingSeries.find((s) => s.name === this.existingName);
        return found ? found.metadata || {} : {};
      }
      return this.newMeta || {};
    },
    doneCount() {
      return this.rows.filter((r) => r.status === "done").length;
    },
    canSubmit() {
      return (
        this.effectiveName &&
        this.rows.length > 0 &&
        this.rows.every((r) => r.season >= 1 && r.episode >= 1)
      );
    },
  },
  methods: {
    emitClose() {
      this.$emit("close");
    },
    onFilesChange(e) {
      const files = Array.from(e?.target?.files || []);
      if (!files.length) return;
      if (!this.presetName && this.mode === "new" && !this.newName.trim()) {
        this.newName = guessSeriesName(files[0].name);
      }
      let lastEp = 0;
      this.rows = files.map((file) => {
        const det = detectSeasonEpisode(file.name);
        const episode = det.episode != null ? det.episode : ++lastEp;
        if (det.episode != null) lastEp = det.episode;
        return { file, season: det.season || 1, episode, status: "pending" };
      });
    },
    titleFor(row) {
      const s = (this.effectiveName || "Série").trim();
      return `${s} - S${pad2(row.season)}E${pad2(row.episode)}`;
    },
    stateLabel(row) {
      return { pending: "En attente", uploading: "Envoi…", done: "✓", error: "Échec" }[row.status];
    },
    onAssociated({ metadata }) {
      this.newMeta = metadata || {};
      this.showAssoc = false;
    },
    async uploadAll() {
      this.error = "";
      this.busy = true;
      try {
        for (const row of this.rows) {
          if (row.status === "done") continue;
          row.status = "uploading";
          const ok = await this.uploadOne(row);
          row.status = ok ? "done" : "error";
        }
        if (this.rows.every((r) => r.status === "done")) {
          this.$emit("done");
          this.emitClose();
        } else {
          this.error = "Certains épisodes n'ont pas pu être ajoutés.";
        }
      } finally {
        this.busy = false;
      }
    },
    uploadOne(row) {
      return new Promise((resolve) => {
        const fd = new FormData();
        fd.append("file", row.file);
        fd.append("media_type", "episode");
        fd.append("series_name", this.effectiveName.trim());
        fd.append("season_number", String(row.season));

        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_BASE}/api/upload`, true);
        xhr.setRequestHeader("Authorization", `Bearer ${this.token}`);
        xhr.onload = async () => {
          if (xhr.status < 200 || xhr.status >= 300) return resolve(false);
          let data = {};
          try {
            data = JSON.parse(xhr.responseText || "{}");
          } catch {
            data = {};
          }
          await this.finalize(data.id, row);
          resolve(true);
        };
        xhr.onerror = () => resolve(false);
        xhr.send(fd);
      });
    },
    async finalize(contentId, row) {
      if (!contentId) return;
      const patch = { title: this.titleFor(row) };
      const meta = this.effectiveMeta || {};
      for (const k of ["poster_url", "backdrop_url", "overview", "year", "tmdb_id", "media_type"]) {
        if (meta[k]) patch[k] = meta[k];
      }
      try {
        await fetch(`${API_BASE}/contents/${encodeURIComponent(contentId)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${this.token}` },
          body: JSON.stringify(patch),
        });
      } catch (e) {
        /* best-effort */
      }
    },
  },
};
</script>

<style scoped>
.su-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 400;
}

.su-modal {
  width: 100%;
  max-width: 760px;
  max-height: 88vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.3);
}

.su-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.su-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
}

.su-mode {
  display: flex;
  gap: 1.25rem;
  margin-bottom: 0.6rem;
}

.su-radio {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
  color: #334155;
}

.su-series {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.su-locked {
  margin: 0;
  color: #334155;
}

.su-field {
  flex: 1;
  min-width: 14rem;
  display: grid;
  gap: 0.3rem;
  font-size: 0.88rem;
  color: #334155;
}

.su-field input,
.su-field select {
  padding: 0.55rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.92rem;
  background: #fff;
}

.su-assoc-chosen {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #334155;
}

.su-assoc-poster {
  width: 32px;
  height: 48px;
  object-fit: cover;
  border-radius: 5px;
}

.su-hint {
  font-size: 0.82rem;
  color: #64748b;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 0.55rem 0.7rem;
  margin: 0 0 0.75rem;
}

.su-filebtn {
  display: inline-block;
  margin-bottom: 0.85rem;
}

.su-filebtn input {
  display: none;
}

.su-filebtn span {
  display: inline-block;
  padding: 0.55rem 1rem;
  border-radius: 10px;
  border: 1px solid #c7d2fe;
  background: #eef2ff;
  color: #4338ca;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
}

.su-table {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 0.85rem;
  max-height: 18rem;
  overflow-y: auto;
}

.su-row {
  display: grid;
  grid-template-columns: 1fr 72px 72px 1.4fr 80px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.35rem 0.45rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.82rem;
}

.su-row--head {
  border: none;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  font-size: 0.7rem;
}

.su-col-file,
.su-col-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.su-col-title {
  color: #4338ca;
  font-weight: 600;
}

input.su-col-num {
  width: 100%;
  padding: 0.35rem 0.4rem;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  font-size: 0.82rem;
}

.su-state--done {
  color: #059669;
  font-weight: 700;
}

.su-state--error {
  color: #dc2626;
  font-weight: 700;
}

.su-state--uploading {
  color: #6366f1;
}

.su-error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0 0 0.5rem;
}

.su-actions {
  display: flex;
  gap: 0.6rem;
}
</style>
