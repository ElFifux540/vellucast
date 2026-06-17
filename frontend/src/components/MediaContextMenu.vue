<template>
  <Teleport to="body">
    <div
      v-if="visible && content"
      class="media-ctx-backdrop"
      @mousedown.self="onClose"
    >
      <ul
        class="media-ctx-menu"
        role="menu"
        :style="menuStyle"
        @mousedown.stop
      >
        <li role="menuitem" tabindex="0" @click="pick('info')">Voir les infos</li>
        <li role="menuitem" tabindex="0" @click="pick('overseerr')">
          Corriger l'association (Overseerr)
        </li>
        <li
          v-if="showDoNotOptimize"
          class="media-ctx-item-flag"
          role="menuitem"
          tabindex="0"
          @click="pick('no_optimize')"
        >
          {{ optimizeActionLabel }}
        </li>
        <li
          v-if="showDoNotOptimize"
          class="media-ctx-item-danger"
          role="menuitem"
          tabindex="0"
          @click="pick('delete')"
        >
          Supprimer
        </li>
      </ul>
    </div>
  </Teleport>
</template>

<script>
/** Largeur / hauteur approximatives du menu pour le clamp dans la fenêtre */
const MENU_W = 280;
const MENU_H = 200;

export default {
  name: "MediaContextMenu",
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
    x: {
      type: Number,
      default: 0,
    },
    y: {
      type: Number,
      default: 0,
    },
    content: {
      type: Object,
      default: null,
    },
    /** Réservé aux admins (API PATCH/PUT du flag). */
    showDoNotOptimize: {
      type: Boolean,
      default: true,
    },
  },
  emits: ["close", "action"],
  computed: {
    /** Si l'exclusion est active → proposer de réactiver l'optimisation. */
    optimizeActionLabel() {
      const c = this.content;
      if (!c) return "Ne pas optimiser";
      const v = c.do_not_optimize;
      const excluded =
        v === true ||
        v === 1 ||
        v === "1" ||
        String(v).toLowerCase() === "true";
      return excluded ? "Optimiser" : "Ne pas optimiser";
    },
    menuStyle() {
      const pad = 8;
      const maxX = Math.max(pad, window.innerWidth - MENU_W - pad);
      const maxY = Math.max(pad, window.innerHeight - MENU_H - pad);
      const left = Math.min(Math.max(pad, this.x), maxX);
      const top = Math.min(Math.max(pad, this.y), maxY);
      return {
        left: `${left}px`,
        top: `${top}px`,
        minWidth: `${MENU_W}px`,
      };
    },
  },
  methods: {
    onClose() {
      this.$emit("close");
    },
    pick(type) {
      if (!this.content) return;
      this.$emit("action", { type, content: this.content });
      this.$emit("close");
    },
  },
};
</script>

<style scoped>
.media-ctx-backdrop {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: transparent;
}

.media-ctx-menu {
  position: fixed;
  z-index: 301;
  margin: 0;
  padding: 0.35rem 0;
  list-style: none;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow:
    0 10px 40px rgba(15, 23, 42, 0.15),
    0 2px 8px rgba(15, 23, 42, 0.08);
}

.media-ctx-menu li {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  color: #1e293b;
  cursor: pointer;
  user-select: none;
}

.media-ctx-menu li:hover {
  background: #f1f5f9;
  color: #312e81;
}

.media-ctx-item-flag {
  border-top: 1px solid #f1f5f9;
  margin-top: 0.2rem;
  padding-top: 0.55rem !important;
}

.media-ctx-item-danger {
  color: #dc2626;
  border-top: 1px solid #f1f5f9;
}

.media-ctx-item-danger:hover {
  background: #fef2f2 !important;
  color: #b91c1c !important;
}
</style>
