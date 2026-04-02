<template>
  <div class="browse-backdrop" role="dialog" aria-modal="true" @click.self="$emit('close')">
    <div class="browse-modal">
      <div class="browse-header">
        <h3 class="browse-title">Explorateur serveur</h3>
        <button type="button" class="btn-outline text-sm py-2 px-3" @click="$emit('close')">
          Fermer
        </button>
      </div>

      <p class="browse-path text-xs text-slate-600 break-all">
        {{ currentPath || "…" }}
      </p>

      <div v-if="loading" class="browse-loading text-slate-600">Chargement…</div>
      <p v-else-if="error" class="text-sm text-red-600">{{ error }}</p>

      <ul v-else class="browse-list">
        <li v-if="parentPath">
          <button
            type="button"
            class="browse-item browse-item-dir"
            @click="goTo(parentPath)"
          >
            📁 ..
          </button>
        </li>
        <li v-for="item in items" :key="item.name + item.type">
          <button
            v-if="item.type === 'directory'"
            type="button"
            class="browse-item browse-item-dir"
            @click="openDir(item.name)"
          >
            📁 {{ item.name }}
          </button>
          <button
            v-else
            type="button"
            class="browse-item browse-item-file"
            :class="{ 'browse-item-active': selectedName === item.name }"
            @click="selectFile(item)"
          >
            🎬 {{ item.name }}
          </button>
        </li>
      </ul>

      <div class="browse-footer">
        <button
          type="button"
          class="btn-primary"
          :disabled="!selectedFile"
          @click="confirmSelection"
        >
          Sélectionner ce fichier
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

export default {
  name: "ServerBrowseModal",
  props: {
    token: {
      type: String,
      required: true,
    },
  },
  emits: ["close", "select"],
  data() {
    return {
      currentPath: "",
      parentPath: null,
      items: [],
      loading: false,
      error: "",
      selectedName: "",
      selectedFile: null,
    };
  },
  mounted() {
    this.load(null);
  },
  methods: {
    async load(path) {
      this.loading = true;
      this.error = "";
      this.selectedName = "";
      this.selectedFile = null;
      try {
        const params = new URLSearchParams();
        if (path) params.set("path", path);
        const url = `${API_BASE}/api/files/browse${params.toString() ? `?${params}` : ""}`;
        const response = await fetch(url, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.error = data.detail || `Erreur ${response.status}`;
          this.items = [];
          return;
        }
        this.currentPath = data.path || "";
        this.parentPath = data.parent || null;
        this.items = Array.isArray(data.items) ? data.items : [];
      } catch (e) {
        this.error = "Impossible de lister le dossier.";
        this.items = [];
      } finally {
        this.loading = false;
      }
    },
    openDir(name) {
      const sep = this.currentPath.includes("\\") ? "\\" : "/";
      const next = `${this.currentPath.replace(/[/\\]+$/, "")}${sep}${name}`;
      this.load(next);
    },
    goTo(path) {
      if (path) this.load(path);
    },
    selectFile(item) {
      this.selectedName = item.name;
      this.selectedFile = item;
    },
    confirmSelection() {
      if (!this.selectedFile || this.selectedFile.type !== "file") return;
      const sep = this.currentPath.includes("\\") ? "\\" : "/";
      const fullPath = `${this.currentPath.replace(/[/\\]+$/, "")}${sep}${this.selectedFile.name}`;
      this.$emit("select", {
        path: fullPath,
        name: this.selectedFile.name,
      });
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
.browse-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.browse-modal {
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e3e7f1;
  box-shadow: 0 20px 50px rgba(2, 6, 23, 0.2);
  padding: 1rem;
}

.browse-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.browse-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #0f172a;
}

.browse-path {
  margin-bottom: 0.75rem;
  font-family: ui-monospace, monospace;
}

.browse-loading {
  padding: 1rem 0;
}

.browse-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  max-height: 45vh;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f8fafc;
}

.browse-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.55rem 0.75rem;
  border: none;
  border-bottom: 1px solid #e5e7eb;
  background: transparent;
  font-size: 0.9rem;
  cursor: pointer;
  color: #1e293b;
}

.browse-item:last-child {
  border-bottom: none;
}

.browse-item-dir:hover {
  background: #e0e7ff;
}

.browse-item-file:hover {
  background: #dbeafe;
}

.browse-item-active {
  background: #c7d2fe !important;
  font-weight: 600;
}

.browse-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: flex-end;
}
</style>
