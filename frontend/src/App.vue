<template>
  <main class="app relative min-h-screen font-sans antialiased text-slate-900">
    <!-- Fond mesh + dégradé (écran connexion / accueil) -->
    <div
      class="pointer-events-none fixed inset-0 -z-10 overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-violet-50"
      aria-hidden="true"
    >
      <div
        class="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-300/35 blur-3xl"
      />
      <div
        class="absolute -bottom-24 -right-24 h-[28rem] w-[28rem] rounded-full bg-violet-300/30 blur-3xl"
      />
      <div
        class="absolute left-1/2 top-1/3 h-72 w-72 -translate-x-1/2 rounded-full bg-blue-200/25 blur-3xl"
      />
    </div>

    <transition name="fade-slide" mode="out-in">
      <!-- Accueil : cartes centrées, espacement resserré -->
      <section
        v-if="view === 'home'"
        key="home"
        class="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-4 pb-12 pt-8 sm:px-6"
      >
        <header class="mb-8 max-w-2xl text-center sm:mb-10">
          <p
            class="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600/90"
          >
            Vellucast
          </p>
          <h1
            class="bg-gradient-to-r from-slate-900 via-indigo-900 to-violet-900 bg-clip-text text-3xl font-bold tracking-tight text-transparent sm:text-4xl"
          >
            Bienvenue sur Vellucast
          </h1>
          <p class="mt-3 text-base leading-relaxed text-slate-600 sm:text-lg">
            Accès sécurisé aux contenus, liens temporaires et gestion centralisée de votre bibliothèque.
          </p>
        </header>

        <article
          class="group flex w-full max-w-md flex-col rounded-3xl border border-slate-200/80 bg-white p-8 shadow-2xl shadow-indigo-500/10 ring-1 ring-slate-200/60 transition duration-300 hover:shadow-indigo-500/15 hover:ring-indigo-200/80"
        >
          <div
            class="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/35"
          >
            <svg
              class="h-8 w-8"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
              />
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-slate-900">Se connecter</h2>
          <p class="mt-2 flex-1 text-slate-600 leading-relaxed">
            Connexion par compte, ou via un lien d'accès temporaire.
          </p>
          <button
            type="button"
            class="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/35 transition hover:scale-[1.02] hover:from-indigo-500 hover:to-blue-500 hover:shadow-xl hover:shadow-indigo-500/40 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 active:scale-[0.98]"
            @click="goLogin('account')"
          >
            Se connecter
          </button>
        </article>
      </section>

      <section
        v-else-if="view === 'login'"
        key="login"
        class="mx-auto mt-8 max-w-md rounded-3xl border border-slate-200/80 bg-white p-8 shadow-2xl shadow-slate-900/10 ring-1 ring-slate-200/60 sm:mt-12"
      >
        <h2 class="text-xl font-semibold text-slate-900">Connexion</h2>

        <!-- Onglets : compte classique / lien temporaire -->
        <div class="login-tabs" role="tablist">
          <button
            type="button"
            class="login-tab"
            :class="{ 'login-tab--active': loginMode === 'account' }"
            @click="setLoginMode('account')"
          >
            Compte
          </button>
          <button
            type="button"
            class="login-tab"
            :class="{ 'login-tab--active': loginMode === 'token' }"
            @click="setLoginMode('token')"
          >
            Lien temporaire
          </button>
        </div>

        <!-- Connexion par compte -->
        <form v-if="loginMode === 'account'" @submit.prevent="loginUser">
          <label>
            Nom d'utilisateur
            <input v-model="userForm.username" type="text" autocomplete="username" />
          </label>
          <label>
            Mot de passe
            <input v-model="userForm.password" type="password" autocomplete="current-password" />
          </label>
          <p v-if="loginError" class="login-error">{{ loginError }}</p>
          <div class="row mt-2">
            <button type="submit" class="btn-primary">Se connecter</button>
            <button type="button" class="btn-outline" @click="view = 'home'">Retour</button>
          </div>
        </form>

        <!-- Connexion par lien temporaire (token + mot de passe du lien facultatif) -->
        <form v-else @submit.prevent="loginGuest">
          <label>
            Token du lien
            <input v-model="guestForm.token" type="text" />
          </label>
          <label>
            Mot de passe du lien (si défini)
            <input v-model="guestForm.access_code" type="password" />
          </label>
          <p v-if="guestError" class="login-error">{{ guestError }}</p>
          <div class="row mt-2">
            <button type="submit" class="btn-primary">Accéder</button>
            <button type="button" class="btn-outline" @click="view = 'home'">Retour</button>
          </div>
        </form>
      </section>

      <section
        v-else-if="view === 'guest-dashboard'"
        key="guest-dashboard"
        class="guest-dashboard w-full px-4 py-2 sm:px-6 lg:px-10"
      >
        <nav class="nav">
          <div class="nav-left">
            <span class="app-brand" title="Vellucast">Vellucast</span>
            <span class="role">Invité</span>
          </div>
          <div class="nav-actions">
            <button class="ghost" @click="exitGuest">Quitter</button>
          </div>
        </nav>
        <GuestLibrary :token="token" :contents="guestContents" />
      </section>

      <section
        v-else-if="view === 'guest-result'"
        key="guest-result"
        class="mx-auto mt-8 max-w-md rounded-3xl border border-slate-200/80 bg-white p-8 shadow-2xl shadow-slate-900/10 ring-1 ring-slate-200/60 sm:mt-12"
      >
        <h2 class="text-xl font-semibold text-slate-900">{{ guestStatusTitle }}</h2>
        <p class="text-slate-600">{{ guestStatusMessage }}</p>
        <p v-if="guestContent" class="text-slate-700">Contenu : {{ guestContent.title }}</p>
        <button type="button" class="btn-outline mt-4 w-full sm:w-auto" @click="view = 'home'">
          Retour accueil
        </button>
      </section>

      <section v-else key="dashboard" class="dashboard w-full px-4 py-2 sm:px-6 lg:px-10">
        <nav class="nav">
          <div class="nav-left">
            <span class="app-brand" title="Vellucast">Vellucast</span>
            <strong class="nav-user">{{ user?.username }}</strong>
            <span class="role">{{ user?.role }}</span>
            <button
              v-if="dashboardView === 'settings'"
              type="button"
              class="ghost"
              @click="dashboardView = 'library'"
            >
              ← Bibliothèque
            </button>
          </div>
          <div class="nav-actions">
            <button
              v-if="dashboardView === 'library'"
              type="button"
              class="ghost text-xl leading-none"
              title="Paramètres"
              aria-label="Paramètres"
              @click="dashboardView = 'settings'"
            >
              ⚙️
            </button>
            <button class="ghost" @click="logout">Se déconnecter</button>
          </div>
        </nav>

        <template v-if="dashboardView === 'library'">
          <transition name="fade-slide" mode="out-in">
            <Library
              v-if="browseView === 'catalog'"
              key="library-view"
              :token="token"
              :is-admin="user?.role === 'admin'"
              @play="onSelectContent"
            />
            <VideoPlayer
              v-else
              key="player-view"
              :token="token"
              :content="selectedContent"
              @back="onBackFromPlayer"
            />
          </transition>
        </template>

        <Settings v-else />

        <UploadMediaModal
          v-if="showUploadModal"
          :token="token"
          @close="showUploadModal = false"
          @uploaded="onMediaUploaded"
        />
      </section>
    </transition>
  </main>
</template>

<script>
import Library from "./components/Library.vue";
import Settings from "./components/Settings.vue";
import VideoPlayer from "./components/VideoPlayer.vue";
import UploadMediaModal from "./components/UploadMediaModal.vue";
import GuestLibrary from "./components/GuestLibrary.vue";
import { API_BASE } from "./config.js";

/** Normalise le champ FastAPI `detail` (string ou liste de validation). */
function formatApiDetail(data) {
  if (!data || typeof data !== "object") return "";
  const d = data.detail ?? data.error;
  if (d == null) return "";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d
      .map((x) => (typeof x === "object" && x.msg ? x.msg : String(x)))
      .join(" ");
  }
  return String(d);
}

export default {
  components: { Library, Settings, VideoPlayer, UploadMediaModal, GuestLibrary },
  provide() {
    return {
      dashboardApp: this,
    };
  },
  data() {
    return {
      view: "home",
      loginMode: "account",
      loginError: "",
      guestError: "",
      userForm: { username: "", password: "" },
      guestForm: { token: "", access_code: "" },
      token: "",
      user: null,
      users: [],
      contents: [],
      shares: [],
      showPassword: false,
      lastShareToken: "",
      guestContent: null,
      guestContents: [],
      guestStatusTitle: "Accès invité",
      guestStatusMessage: "",
      passwordForm: {
        current_password: "",
        new_password: "",
        new_password_confirm: "",
      },
      adminUserForm: {
        username: "",
        password: "",
        role: "user",
        must_change_password: false,
      },
      updateUserForm: {
        username: "",
        new_username: "",
        role: "",
        must_change_password: false,
      },
      resetPasswordForm: {
        username: "",
        new_password: "",
        must_change_password: true,
      },
      contentForm: {
        id: "",
        title: "",
        media_path: "",
        media_kind: "movie",
        series_name: "",
        season_number: null,
        episode_number: null,
      },
      contentUpdateForm: {
        id: "",
        title: "",
        media_path: "",
      },
      shareForm: {
        content_id: "",
        content_ids: [],
        expires_in_value: 7,
        expires_in_unit: "days",
        max_uses: 1,
        access_code: "",
      },
      browseView: "catalog",
      selectedContent: null,
      showUploadModal: false,
      dashboardView: "library",
    };
  },
  async mounted() {
    await this.restoreSession();
  },
  methods: {
    persistSession() {
      try {
        localStorage.setItem(
          "vellucast_session",
          JSON.stringify({ token: this.token, user: this.user }),
        );
      } catch (e) {
        /* localStorage indisponible : on continue sans persistance */
      }
    },
    clearSession() {
      try {
        localStorage.removeItem("vellucast_session");
      } catch (e) {
        /* no-op */
      }
    },
    async restoreSession() {
      // 1) Session invité : restaurée tant que le jeton vit ; détruite dès qu'il meurt (401).
      let guest = null;
      try {
        guest = JSON.parse(localStorage.getItem("vellucast_guest") || "null");
      } catch (e) {
        guest = null;
      }
      if (guest && guest.token) {
        try {
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${guest.token}` },
          });
          if (res.ok) {
            const data = await res.json();
            if (data.user?.role === "guest") {
              this.token = guest.token;
              this.guestContents = Array.isArray(guest.contents) ? guest.contents : [];
              this.user = { username: "Invité", role: "guest" };
              this.view = "guest-dashboard";
              return;
            }
          }
          this.clearGuestSession(); // jeton mort → session détruite
        } catch (e) {
          this.clearGuestSession();
        }
      }

      // 2) Session « compte » classique.
      // Le cookie cesse de marcher dès que le jeton est expiré/invalide (401 → on nettoie).
      let saved = null;
      try {
        saved = JSON.parse(localStorage.getItem("vellucast_session") || "null");
      } catch (e) {
        saved = null;
      }
      if (!saved || !saved.token) return;
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${saved.token}` },
        });
        if (!res.ok) {
          this.clearSession();
          return;
        }
        const data = await res.json();
        this.token = saved.token;
        this.user = data.user || saved.user || null;
        this.view = "dashboard";
        this.dashboardView = "library";
        await this.loadContents();
        if (this.user?.role === "admin") {
          await this.loadUsers();
          await this.loadShares();
        }
      } catch (e) {
        this.clearSession();
      }
    },
    async onMediaUploaded() {
      await this.loadContents();
      this.showUploadModal = false;
      // Notifie la bibliothèque pour qu'elle rafraîchisse sa propre liste.
      window.dispatchEvent(new Event("vellucast-contents-changed"));
    },
    onSelectContent(content) {
      this.selectedContent = content;
      this.browseView = "player";
    },
    onBackFromPlayer() {
      this.selectedContent = null;
      this.browseView = "catalog";
    },
    goLogin(mode = "account") {
      this.loginError = "";
      this.guestError = "";
      this.loginMode = mode === "token" ? "token" : "account";
      this.view = "login";
    },
    setLoginMode(mode) {
      this.loginMode = mode === "token" ? "token" : "account";
      this.loginError = "";
      this.guestError = "";
    },
    async loginUser() {
      this.loginError = "";
      try {
        const response = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.userForm),
        });
        const data = await response.json().catch(() => ({}));
        // Échec : on reste sur l'écran de connexion avec un message inline.
        if (!response.ok || !data.token) {
          this.loginError = formatApiDetail(data) || "Identifiants invalides.";
          return;
        }
        this.token = data.token;
        this.user = data.user || null;
        this.persistSession();
        this.view = "dashboard";
        this.dashboardView = "library";
        await this.loadContents();
        if (this.user?.role === "admin") {
          await this.loadUsers();
          await this.loadShares();
        }
      } catch (error) {
        this.loginError = "Impossible de joindre le serveur.";
      }
    },
    async loginGuest() {
      this.guestError = "";
      try {
        const response = await fetch(`${API_BASE}/auth/guest`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.guestForm),
        });
        const data = await response.json().catch(() => ({}));
        // Échec : on reste sur l'écran de connexion (onglet lien) avec un message inline.
        if (!response.ok || !data.token) {
          this.guestError = formatApiDetail(data) || "Lien ou mot de passe invalide.";
          return;
        }
        // Le serveur renvoie un jeton invité scopé + la liste des contenus autorisés.
        this.token = data.token;
        this.guestContents = Array.isArray(data.contents) ? data.contents : [];
        this.user = { username: "Invité", role: "guest" };
        this.persistGuestSession();
        this.view = "guest-dashboard";
      } catch (error) {
        this.guestError = "Impossible de joindre le serveur.";
      }
    },
    persistGuestSession() {
      try {
        localStorage.setItem(
          "vellucast_guest",
          JSON.stringify({ token: this.token, contents: this.guestContents }),
        );
      } catch (e) {
        /* no-op */
      }
    },
    clearGuestSession() {
      try {
        localStorage.removeItem("vellucast_guest");
      } catch (e) {
        /* no-op */
      }
    },
    exitGuest() {
      // Quitter la session invité (le jeton reste valide jusqu'à son expiration côté serveur).
      this.clearGuestSession();
      this.token = "";
      this.user = null;
      this.guestContents = [];
      this.view = "home";
    },
    async changePassword() {
      if (this.passwordForm.new_password !== this.passwordForm.new_password_confirm) {
        console.warn("Confirmation mot de passe invalide");
        return;
      }
      try {
        const response = await fetch(`${API_BASE}/auth/change-password`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify({
            current_password: this.passwordForm.current_password,
            new_password: this.passwordForm.new_password,
          }),
        });
        const data = await response.json();
        console.log("changePassword", data);
        if (data.ok) {
          this.passwordForm.current_password = "";
          this.passwordForm.new_password = "";
          this.passwordForm.new_password_confirm = "";
          this.showPassword = false;
        }
      } catch (error) {
        console.error("changePassword error", error);
      }
    },
    async createUser() {
      try {
        const response = await fetch(`${API_BASE}/admin/users`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify(this.adminUserForm),
        });
        const data = await response.json().catch(() => ({}));
        console.log("createUser", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        await this.loadUsers();
        return { ok: true };
      } catch (error) {
        console.error("createUser error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async updateUser() {
      try {
        const response = await fetch(`${API_BASE}/admin/users`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify(this.updateUserForm),
        });
        const data = await response.json().catch(() => ({}));
        console.log("updateUser", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        await this.loadUsers();
        return { ok: true };
      } catch (error) {
        console.error("updateUser error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async updateUserRoleFromList(userRow, newRole) {
      if (!userRow?.username || newRole === userRow.role) {
        return { ok: true, skipped: true };
      }
      try {
        const response = await fetch(`${API_BASE}/admin/users`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify({
            username: userRow.username,
            role: newRole,
          }),
        });
        const data = await response.json().catch(() => ({}));
        console.log("updateUserRoleFromList", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        await this.loadUsers();
        return { ok: true };
      } catch (error) {
        console.error("updateUserRoleFromList error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async resetUserPassword() {
      try {
        const response = await fetch(`${API_BASE}/admin/users/reset-password`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify(this.resetPasswordForm),
        });
        const data = await response.json().catch(() => ({}));
        console.log("resetUserPassword", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        await this.loadUsers();
        return { ok: true };
      } catch (error) {
        console.error("resetUserPassword error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async loadUsers() {
      try {
        const response = await fetch(`${API_BASE}/admin/users`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        const data = await response.json();
        console.log("loadUsers", data);
        this.users = Array.isArray(data) ? data : [];
      } catch (error) {
        console.error("loadUsers error", error);
      }
    },
    generateShortContentId() {
      const alphabet =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
      const bytes = new Uint8Array(8);
      crypto.getRandomValues(bytes);
      return Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
    },
    resetContentCreateForm() {
      this.contentForm.id = this.generateShortContentId();
      this.contentForm.title = "";
      this.contentForm.media_path = "";
      this.contentForm.media_kind = "movie";
      this.contentForm.series_name = "";
      this.contentForm.season_number = null;
      this.contentForm.episode_number = null;
    },
    computeContentTitleForCreate() {
      const base = (this.contentForm.title || "").trim();
      if (this.contentForm.media_kind === "movie") {
        return base;
      }
      const sn = (this.contentForm.series_name || "").trim();
      const season = this.contentForm.season_number;
      const ep = this.contentForm.episode_number;
      return `${sn} - Saison ${season} - Ép. ${ep} - ${base}`;
    },
    async createContent() {
      try {
        const body = {
          id: (this.contentForm.id || "").trim(),
          title: this.computeContentTitleForCreate(),
          media_path: (this.contentForm.media_path || "").trim(),
        };
        const response = await fetch(`${API_BASE}/contents`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify(body),
        });
        const data = await response.json().catch(() => ({}));
        console.log("createContent", data);
        if (!response.ok) {
          return { ok: false, detail: data.detail || data.error || `Erreur ${response.status}` };
        }
        await this.loadContents();
        this.resetContentCreateForm();
        return { ok: true };
      } catch (error) {
        console.error("createContent error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async updateContent() {
      const id = (this.contentUpdateForm.id || "").trim();
      if (!id) {
        return { ok: false, detail: "Aucun contenu sélectionné." };
      }
      const title = (this.contentUpdateForm.title || "").trim();
      if (!title) {
        return { ok: false, detail: "Le titre ne peut pas être vide." };
      }
      const mediaPath = (this.contentUpdateForm.media_path || "").trim();
      try {
        const response = await fetch(
          `${API_BASE}/contents/${encodeURIComponent(id)}`,
          {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${this.token}`,
            },
            body: JSON.stringify({
              title,
              media_path: mediaPath || undefined,
            }),
          }
        );
        const data = await response.json().catch(() => ({}));
        console.log("updateContent", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: data.detail || data.error || `Erreur ${response.status}`,
          };
        }
        await this.loadContents();
        return { ok: true };
      } catch (error) {
        console.error("updateContent error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async deleteContent(contentId) {
      try {
        const response = await fetch(
          `${API_BASE}/contents/${encodeURIComponent(contentId)}`,
          {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${this.token}`,
            },
          }
        );
        const data = await response.json();
        console.log("deleteContent", data);
        await this.loadContents();
      } catch (error) {
        console.error("deleteContent error", error);
      }
    },
    async createShare() {
      try {
        const response = await fetch(`${API_BASE}/shares`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.token}`,
          },
          body: JSON.stringify(this.shareForm),
        });
        const data = await response.json().catch(() => ({}));
        console.log("createShare", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        this.lastShareToken = data.token || "";
        this.shareForm.content_ids = [];
        await this.loadShares();
        return { ok: true };
      } catch (error) {
        console.error("createShare error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    /** Révoque ou supprime définitivement une entrée (DELETE côté API). */
    async revokeShare(token) {
      try {
        const response = await fetch(
          `${API_BASE}/admin/shares/${encodeURIComponent(token)}`,
          {
            method: "DELETE",
            headers: { Authorization: `Bearer ${this.token}` },
          }
        );
        const data = await response.json().catch(() => ({}));
        console.log("revokeShare", data);
        if (!response.ok) {
          return {
            ok: false,
            detail: formatApiDetail(data) || `Erreur ${response.status}`,
          };
        }
        await this.loadShares();
        return { ok: true };
      } catch (error) {
        console.error("revokeShare error", error);
        return { ok: false, detail: "Erreur réseau" };
      }
    },
    async loadContents() {
      try {
        const response = await fetch(`${API_BASE}/contents`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        const data = await response.json();
        console.log("loadContents", data);
        this.contents = Array.isArray(data) ? data : [];
      } catch (error) {
        console.error("loadContents error", error);
      }
    },
    /**
     * Met à jour le flag do_not_optimize en local après toggle (sans recharger la liste).
     */
    applyContentDoNotOptimizeToggle(contentId, doNotOptimize) {
      const id = String(contentId || "");
      const idx = this.contents.findIndex((c) => c && c.id === id);
      if (idx < 0) return;
      const row = this.contents[idx];
      const next = Boolean(doNotOptimize);
      this.contents.splice(idx, 1, { ...row, do_not_optimize: next });
    },
    async loadShares() {
      try {
        const response = await fetch(`${API_BASE}/admin/shares`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });
        const data = await response.json();
        console.log("loadShares", data);
        this.shares = Array.isArray(data) ? data : [];
      } catch (error) {
        console.error("loadShares error", error);
      }
    },
    async copyToken(value) {
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
      } catch (error) {
        console.error("copyToken error", error);
      }
    },
    logout() {
      this.clearSession();
      this.clearGuestSession();
      this.guestContents = [];
      this.token = "";
      this.user = null;
      this.users = [];
      this.contents = [];
      this.shares = [];
      this.lastShareToken = "";
      this.guestContent = null;
      this.browseView = "catalog";
      this.selectedContent = null;
      this.showUploadModal = false;
      this.dashboardView = "library";
      this.loginMode = "account";
      this.loginError = "";
      this.guestError = "";
      this.userForm = { username: "", password: "" };
      this.guestForm = { token: "", access_code: "" };
      this.view = "home";
    },
  },
};
</script>

<style scoped>
.app {
  min-height: 100vh;
}

.dashboard,
.guest-dashboard {
  background: transparent;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 100vh;
}

.card,
.dashboard :deep(.card) {
  border: 1px solid #e3e7f1;
  border-radius: 14px;
  padding: 1.5rem;
  background: #ffffff;
  box-shadow: 0 12px 30px rgba(16, 24, 40, 0.08);
  display: grid;
  gap: 1rem;
}

.row {
  display: flex;
  gap: 0.75rem;
}

label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.95rem;
  color: #1f2937;
}

input {
  padding: 0.6rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
}

.login-tabs {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0 1.25rem;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 12px;
}

.login-tab {
  flex: 1;
  padding: 0.55rem 0.75rem;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: #475569;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.login-tab--active {
  background: #fff;
  color: #312e81;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.12);
}

.login-error {
  margin: 0.75rem 0 0;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  font-size: 0.88rem;
}

.ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  border: 2px solid rgb(99 102 241);
  background: #fff;
  color: rgb(79 70 229);
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  transition:
    transform 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease;
}

.ghost:hover {
  border-color: rgb(79 70 229);
  background: rgb(238 242 255);
  color: rgb(67 56 202);
}

.cta {
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  color: #fff;
}

.nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid #e5e7eb;
}

.nav-left {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.app-brand {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #312e81 0%, #4f46e5 45%, #7c3aed 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  padding-right: 0.5rem;
  margin-right: 0.25rem;
  border-right: 1px solid #e2e8f0;
}

.nav-user {
  font-weight: 600;
  color: #1e293b;
}

.role {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  font-size: 0.85rem;
}

.dashboard :deep(.admin-grid) {
  display: grid;
  gap: 1rem;
}

.dashboard :deep(.checkbox) {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dashboard :deep(.token-box) {
  margin-top: 0.5rem;
  padding: 0.75rem;
  border-radius: 10px;
  background: #f3f4f6;
}

.dashboard :deep(.token-row) {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.dashboard :deep(.duration-row) {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.dashboard :deep(select) {
  padding: 0.6rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
  background: #fff;
}

.dashboard :deep(code) {
  background: #111827;
  color: #f9fafb;
  padding: 0.35rem 0.6rem;
  border-radius: 6px;
  font-size: 0.85rem;
}

.dashboard :deep(.muted) {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1rem;
}

.dashboard :deep(.list) {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
}

.dashboard :deep(.list-row) {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem 0;
}

.dashboard :deep(.meta) {
  color: #6b7280;
  font-size: 0.85rem;
  margin-top: 0.2rem;
  word-break: break-word;
}

.dashboard :deep(.list ul) {
  margin: 0;
  padding-left: 1.1rem;
  color: #374151;
}

.dashboard :deep(label) {
  display: grid;
  gap: 0.35rem;
  font-size: 0.95rem;
  color: #1f2937;
}

.dashboard :deep(input) {
  padding: 0.6rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
}

.dashboard :deep(.row) {
  display: flex;
  gap: 0.75rem;
}

.dashboard :deep(.ghost) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 1rem;
  border: 2px solid rgb(99 102 241);
  background: #fff;
  color: rgb(79 70 229);
  font-weight: 600;
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  transition:
    transform 0.15s ease,
    background 0.15s ease,
    border-color 0.15s ease;
}

.dashboard :deep(.ghost):hover {
  border-color: rgb(79 70 229);
  background: rgb(238 242 255);
  color: rgb(67 56 202);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(6px);
}
</style>

