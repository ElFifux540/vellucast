<template>
  <Teleport to="body">
    <div v-if="visible && seriesName" class="series-ctx-backdrop" @mousedown.self="$emit('close')">
      <ul class="series-ctx-menu" role="menu" :style="menuStyle" @mousedown.stop>
        <li class="series-ctx-head">{{ seriesName }}</li>
        <li role="menuitem" tabindex="0" @click="pick('associate')">
          Corriger l'association (Overseerr)
        </li>
        <li role="menuitem" tabindex="0" @click="pick('add-episode')">Ajouter un épisode</li>
        <li
          v-for="target in mergeCandidates"
          :key="target"
          role="menuitem"
          tabindex="0"
          class="series-ctx-merge"
          @click="pickMerge(target)"
        >
          Fusionner avec « {{ target }} »
        </li>
        <li role="menuitem" tabindex="0" class="series-ctx-danger" @click="pick('delete-series')">
          Supprimer la série
        </li>
      </ul>
    </div>
  </Teleport>
</template>

<script>
const MENU_W = 280;
const MENU_H = 220;

export default {
  name: "SeriesContextMenu",
  props: {
    visible: { type: Boolean, default: false },
    x: { type: Number, default: 0 },
    y: { type: Number, default: 0 },
    seriesName: { type: String, default: "" },
    mergeCandidates: { type: Array, default: () => [] },
  },
  emits: ["close", "action"],
  computed: {
    menuStyle() {
      const pad = 8;
      const maxX = Math.max(pad, window.innerWidth - MENU_W - pad);
      const maxY = Math.max(pad, window.innerHeight - MENU_H - pad);
      return {
        left: `${Math.min(Math.max(pad, this.x), maxX)}px`,
        top: `${Math.min(Math.max(pad, this.y), maxY)}px`,
        minWidth: `${MENU_W}px`,
      };
    },
  },
  methods: {
    pick(type) {
      this.$emit("action", { type, seriesName: this.seriesName });
      this.$emit("close");
    },
    pickMerge(target) {
      this.$emit("action", { type: "merge", seriesName: this.seriesName, target });
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
.series-ctx-backdrop {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: transparent;
}

.series-ctx-menu {
  position: fixed;
  z-index: 301;
  margin: 0;
  padding: 0.35rem 0;
  list-style: none;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 10px 40px rgba(15, 23, 42, 0.15), 0 2px 8px rgba(15, 23, 42, 0.08);
}

.series-ctx-head {
  padding: 0.35rem 1rem 0.5rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 0.2rem;
}

.series-ctx-menu li[role="menuitem"] {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  color: #1e293b;
  cursor: pointer;
  user-select: none;
}

.series-ctx-menu li[role="menuitem"]:hover {
  background: #f1f5f9;
  color: #312e81;
}

.series-ctx-merge {
  color: #4f46e5;
}

.series-ctx-danger {
  color: #dc2626;
  border-top: 1px solid #f1f5f9;
  margin-top: 0.2rem;
}

.series-ctx-danger:hover {
  background: #fef2f2 !important;
  color: #b91c1c !important;
}
</style>
