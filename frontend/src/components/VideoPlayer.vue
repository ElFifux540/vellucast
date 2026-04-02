<template>
  <div
    class="video-player rounded-2xl border border-slate-200/80 bg-white p-6 shadow-lg ring-1 ring-slate-200/60"
  >
    <button
      type="button"
      class="btn-outline mb-4"
      @click="$emit('back')"
    >
      ← Retour au catalogue
    </button>

    <h2 class="mb-4 text-xl font-semibold text-slate-900">{{ content.title }}</h2>

    <div class="overflow-hidden rounded-xl bg-black shadow-inner ring-1 ring-slate-800/20">
      <video
        v-if="streamUrl"
        :key="streamUrl"
        :src="streamUrl"
        controls
        playsinline
        preload="metadata"
        crossorigin="anonymous"
        class="max-h-[72vh] w-full"
      />
    </div>
    <p v-if="!streamUrl" class="text-slate-600">Session invalide : impossible de lire la vidéo.</p>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

export default {
  name: "VideoPlayer",
  props: {
    token: {
      type: String,
      required: true,
    },
    content: {
      type: Object,
      required: true,
    },
  },
  emits: ["back"],
  computed: {
    streamUrl() {
      if (!this.token || !this.content?.id) return "";
      const id = encodeURIComponent(this.content.id);
      const t = encodeURIComponent(this.token);
      return `${API_BASE}/api/stream/${id}?token=${t}`;
    },
  },
};
</script>
