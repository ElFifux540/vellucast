<template>
  <div class="video-player">
    <button type="button" class="vp-back" @click="$emit('back')">← Retour</button>

    <h2 class="vp-title">{{ content.title }}</h2>

    <div class="vp-stage">
      <video ref="video" class="vp-video" playsinline crossorigin="anonymous" controls />
    </div>

    <p v-if="statusMessage" class="vp-status" :class="{ 'vp-status--error': statusIsError }">
      {{ statusMessage }}
    </p>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";

// Chargement dynamique de Plyr (CSS + JS) et hls.js depuis le CDN (aucune dépendance de build).
const PLYR_CSS = "https://cdn.plyr.io/3.7.8/plyr.css";
const PLYR_JS = "https://cdn.plyr.io/3.7.8/plyr.polyfilled.js";
const HLS_JS = "https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js";

let plyrPromise = null;
let hlsPromise = null;

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Échec de chargement : " + src));
    document.head.appendChild(s);
  });
}

function loadPlyr() {
  if (window.Plyr) return Promise.resolve(window.Plyr);
  if (plyrPromise) return plyrPromise;
  if (!document.querySelector("link[data-plyr]")) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = PLYR_CSS;
    link.setAttribute("data-plyr", "1");
    document.head.appendChild(link);
  }
  plyrPromise = loadScript(PLYR_JS).then(() => window.Plyr);
  return plyrPromise;
}

function loadHls() {
  if (window.Hls) return Promise.resolve(window.Hls);
  if (hlsPromise) return hlsPromise;
  hlsPromise = loadScript(HLS_JS).then(() => window.Hls);
  return hlsPromise;
}

const PLYR_OPTIONS = {
  controls: [
    "play-large",
    "rewind",
    "play",
    "fast-forward",
    "progress",
    "current-time",
    "duration",
    "mute",
    "volume",
    "settings",
    "pip",
    "fullscreen",
  ],
  settings: ["speed"],
  speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
  keyboard: { focused: true, global: true },
};

export default {
  name: "VideoPlayer",
  props: {
    token: { type: String, required: true },
    content: { type: Object, required: true },
  },
  emits: ["back"],
  data() {
    return { statusMessage: "", statusIsError: false, plyr: null, hls: null };
  },
  computed: {
    rawStreamUrl() {
      const id = encodeURIComponent(this.content.id);
      const t = encodeURIComponent(this.token);
      return `${API_BASE}/api/stream/${id}?token=${t}`;
    },
    hlsPlaylistUrl() {
      const id = encodeURIComponent(this.content.id);
      return `${API_BASE}/api/stream/${id}/hls/index.m3u8`;
    },
  },
  async mounted() {
    await this.setupPlayback();
  },
  beforeUnmount() {
    this.teardown();
  },
  methods: {
    teardown() {
      if (this.plyr) {
        try {
          this.plyr.destroy();
        } catch (e) {
          /* no-op */
        }
        this.plyr = null;
      }
      if (this.hls) {
        try {
          this.hls.destroy();
        } catch (e) {
          /* no-op */
        }
        this.hls = null;
      }
    },
    async initPlyr() {
      const Plyr = await loadPlyr();
      const video = this.$refs.video;
      if (!video || !Plyr) return;
      this.plyr = new Plyr(video, PLYR_OPTIONS);
    },
    async setupPlayback() {
      if (!this.token || !this.content?.id) {
        this.statusIsError = true;
        this.statusMessage = "Session invalide : impossible de lire la vidéo.";
        return;
      }

      let decision = { mode: "direct" };
      try {
        const res = await fetch(
          `${API_BASE}/api/stream/${encodeURIComponent(this.content.id)}/info`,
          { headers: { Authorization: `Bearer ${this.token}` } },
        );
        if (res.ok) decision = await res.json();
      } catch (e) {
        /* repli lecture directe */
      }

      if (decision.mode === "hls") {
        this.statusMessage = "Transcodage à la volée (HLS) — " + (decision.reason || "");
        await this.playHls();
      } else {
        this.statusMessage = "";
        await this.playDirect();
      }
    },
    async playDirect() {
      const video = this.$refs.video;
      if (!video) return;
      video.src = this.rawStreamUrl;
      await this.initPlyr();
    },
    async playHls() {
      const video = this.$refs.video;
      if (!video) return;

      // Safari / iOS : HLS natif (token en query, pas d'en-tête possible sur <video>).
      if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = `${this.hlsPlaylistUrl}?token=${encodeURIComponent(this.token)}`;
        await this.initPlyr();
        return;
      }

      try {
        const Hls = await loadHls();
        if (!Hls || !Hls.isSupported()) {
          this.statusIsError = true;
          this.statusMessage = "Votre navigateur ne supporte pas la lecture HLS.";
          return;
        }
        const token = this.token;
        this.hls = new Hls({
          xhrSetup(xhr) {
            xhr.setRequestHeader("Authorization", `Bearer ${token}`);
          },
        });
        this.hls.loadSource(this.hlsPlaylistUrl);
        this.hls.attachMedia(video);
        this.hls.on(Hls.Events.ERROR, (_e, data) => {
          if (data.fatal) {
            this.statusIsError = true;
            this.statusMessage = "Erreur de lecture HLS : " + (data.details || data.type || "");
          }
        });
        await this.initPlyr();
      } catch (e) {
        this.statusIsError = true;
        this.statusMessage = "Impossible de charger le lecteur HLS.";
      }
    },
  },
};
</script>

<style scoped>
.video-player {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.vp-back {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: background 0.15s ease;
}

.vp-back:hover {
  background: #eef2ff;
}

.vp-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.vp-stage {
  width: 100%;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(2, 6, 23, 0.4);
}

.vp-video {
  width: 100%;
  max-height: 80vh;
  display: block;
}

/* Accent Plyr aux couleurs Vellucast */
.video-player :deep(.plyr) {
  --plyr-color-main: #6366f1;
  border-radius: 16px;
}

/* Plein écran : centrer la vidéo (sinon elle se colle en haut sur un ratio inhabituel). */
.video-player :deep(.plyr--fullscreen-active .plyr__video-wrapper) {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
  background: #000;
}

.video-player :deep(.plyr--fullscreen-active video) {
  position: relative;
  height: auto;
  max-height: 100%;
  width: auto;
  max-width: 100%;
  margin: auto;
  object-fit: contain;
}

.vp-status {
  font-size: 0.85rem;
  color: #64748b;
}

.vp-status--error {
  color: #dc2626;
}
</style>
