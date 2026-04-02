<template>
  <div
    class="catalog rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg ring-1 ring-slate-200/60"
  >
    <h2 class="mb-1 text-lg font-semibold text-slate-900">Bibliothèque Vellucast</h2>
    <p class="mb-4 text-sm text-slate-600">Sélectionnez un film pour le lire.</p>

    <p v-if="loading" class="text-slate-600">Chargement…</p>
    <p v-else-if="error" class="text-red-600">{{ error }}</p>
    <p v-else-if="items.length === 0" class="text-slate-600">Aucun contenu disponible.</p>

    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <button
        v-for="c in items"
        :key="c.id"
        type="button"
        class="group flex min-h-[5.5rem] flex-col rounded-xl border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-4 text-left shadow-sm transition hover:border-indigo-300 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="$emit('select', c)"
      >
        <span class="font-semibold text-slate-900 group-hover:text-indigo-800">{{ c.title }}</span>
        <span class="mt-auto truncate pt-2 text-xs text-slate-500">{{ c.id }}</span>
      </button>
    </div>
  </div>
</template>

<script>
/**
 * Ancienne grille catalogue — remplacée par Library.vue (onglets + zone hero).
 * Conservé pour référence ; non monté dans App.vue.
 */
import { API_BASE } from "../config.js";

export default {
  name: "Catalog",
  props: {
    token: {
      type: String,
      required: true,
    },
  },
  emits: ["select"],
  data() {
    return {
      items: [],
      loading: true,
      error: "",
    };
  },
  async mounted() {
    await this.fetchContents();
  },
  methods: {
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
  },
};
</script>
