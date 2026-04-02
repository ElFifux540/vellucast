<template>
  <div class="settings-view space-y-6">
    <h1 class="settings-page-title text-2xl font-bold tracking-tight text-slate-900">
      <span class="settings-brand">Vellucast</span>
      <span class="settings-page-sub">Paramètres</span>
    </h1>

    <section v-if="dashboardApp.user?.role === 'admin'" class="card">
      <h2>Dossiers médias Vellucast</h2>
      <p class="text-sm text-slate-600">
        Dossiers de base utilisés pour les uploads (films et séries). Les chemins doivent rester sous
        <code class="rounded bg-slate-100 px-1 py-0.5 text-xs">MEDIA_FOLDER</code> si celui-ci est défini côté serveur.
      </p>
      <form class="mt-4 grid gap-3" @submit.prevent="saveFolderSettings">
        <label>
          Dossier de base pour les Films
          <input v-model="folderForm.movies_folder" type="text" :disabled="folderSaving" />
        </label>
        <label>
          Dossier de base pour les Séries
          <input v-model="folderForm.series_folder" type="text" :disabled="folderSaving" />
        </label>
        <div class="row">
          <button type="submit" class="btn-primary" :disabled="folderSaving">
            {{ folderSaving ? "Enregistrement…" : "Sauvegarder" }}
          </button>
        </div>
        <p v-if="folderMessage" class="text-sm text-emerald-700">{{ folderMessage }}</p>
        <p v-if="folderError" class="text-sm text-red-600">{{ folderError }}</p>
      </form>
    </section>

    <section v-if="dashboardApp.user?.role === 'admin'" class="card transcoding-settings-card">
      <h2>Paramètres de Transcodage</h2>
      <p class="mb-4 text-sm text-slate-600">
        Réglages du transcodage en direct et de l’optimisation automatique (persistés en base,
        clés <code class="rounded bg-slate-100 px-1 text-xs">app_settings</code>).
      </p>
      <form class="transcoding-form grid gap-4" @submit.prevent="saveTranscodingSettings">
        <label class="transcoding-checkbox">
          <input v-model="transcodeForm.stream_transcode_enabled" type="checkbox" />
          <span>Activer le transcodage à la volée pendant le streaming</span>
        </label>

        <div
          v-if="transcodeForm.stream_transcode_enabled"
          class="transcode-quality-block rounded-xl border border-slate-200 bg-slate-50/80 p-4"
        >
          <label class="mb-2 block text-sm font-medium text-slate-800">
            Qualité du transcodage
          </label>
          <input
            v-model.number="transcodeForm.stream_transcode_preset"
            type="range"
            min="1"
            max="5"
            step="1"
            class="transcode-range w-full max-w-lg"
          />
          <p class="mt-2 text-sm text-slate-600">{{ transcodeQualityLabel }}</p>
        </div>

        <label class="transcoding-checkbox">
          <input v-model="transcodeForm.auto_optimize_enabled" type="checkbox" />
          <span>Activer l’optimisation automatique des fichiers</span>
        </label>

        <div
          v-if="transcodeForm.auto_optimize_enabled"
          class="auto-optimize-panel grid gap-4 border-l-4 border-indigo-200 pl-4"
        >
          <label>
            Paramètres FFmpeg exacts
            <input
              v-model="transcodeForm.ffmpeg_params"
              type="text"
              placeholder="-vcodec libx264 -preset fast"
              autocomplete="off"
            />
          </label>

          <fieldset class="optimize-trigger-fieldset">
            <legend class="mb-2 text-sm font-medium text-slate-700">Déclenchement</legend>
            <label class="transcoding-radio">
              <input
                v-model="transcodeForm.optimize_schedule_type"
                type="radio"
                value="upload"
              />
              <span>Immédiatement après upload</span>
            </label>
            <label class="transcoding-radio">
              <input
                v-model="transcodeForm.optimize_schedule_type"
                type="radio"
                value="scheduled"
              />
              <span>Pendant des heures planifiées</span>
            </label>
          </fieldset>

          <div
            v-if="transcodeForm.optimize_schedule_type === 'scheduled'"
            class="schedule-times flex flex-wrap gap-6"
          >
            <label>
              Heure de début
              <input v-model="transcodeForm.optimize_start_time" type="time" />
            </label>
            <label>
              Heure de fin
              <input v-model="transcodeForm.optimize_end_time" type="time" />
            </label>
          </div>
        </div>

        <div class="row">
          <button type="submit" class="btn-primary" :disabled="transcodeSaving">
            {{ transcodeSaving ? "Enregistrement…" : "Sauvegarder" }}
          </button>
        </div>
        <p v-if="transcodeMessage" class="text-sm text-emerald-700">{{ transcodeMessage }}</p>
        <p v-if="transcodeError" class="text-sm text-red-600">{{ transcodeError }}</p>
      </form>
    </section>

    <section v-if="dashboardApp.user?.role === 'admin'" class="card">
      <h2>Utilisateurs Vellucast</h2>
      <div class="admin-grid">
        <form @submit.prevent="submitCreateUser">
          <h3>Créer un user</h3>
          <label>
            Username
            <input v-model="dashboardApp.adminUserForm.username" type="text" />
          </label>
          <label>
            Mot de passe
            <input v-model="dashboardApp.adminUserForm.password" type="password" />
          </label>
          <label>
            Rôle
            <select v-model="dashboardApp.adminUserForm.role" class="role-select">
              <option v-for="r in allowedRoles" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
          <label class="checkbox">
            <input v-model="dashboardApp.adminUserForm.must_change_password" type="checkbox" />
            Forcer changement
          </label>
          <button type="submit" class="btn-primary">Créer</button>
          <p v-if="userCreateSuccess" class="feedback-success">{{ userCreateSuccess }}</p>
          <p v-if="userCreateError" class="feedback-error">{{ userCreateError }}</p>
        </form>

        <form @submit.prevent="submitUpdateUser">
          <h3>Mettre à jour un user</h3>
          <label>
            Username actuel
            <input v-model="dashboardApp.updateUserForm.username" type="text" />
          </label>
          <label>
            Nouveau username (optionnel)
            <input v-model="dashboardApp.updateUserForm.new_username" type="text" />
          </label>
          <label>
            Rôle (optionnel)
            <select v-model="dashboardApp.updateUserForm.role" class="role-select">
              <option value="">— Ne pas modifier —</option>
              <option v-for="r in allowedRoles" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
          <label class="checkbox">
            <input v-model="dashboardApp.updateUserForm.must_change_password" type="checkbox" />
            Forcer changement au prochain login
          </label>
          <button type="submit" class="btn-primary">Mettre à jour</button>
          <p v-if="userUpdateSuccess" class="feedback-success">{{ userUpdateSuccess }}</p>
          <p v-if="userUpdateError" class="feedback-error">{{ userUpdateError }}</p>
        </form>

        <form @submit.prevent="submitResetUserPassword">
          <h3>Reset mot de passe</h3>
          <label>
            Username
            <input v-model="dashboardApp.resetPasswordForm.username" type="text" />
          </label>
          <label>
            Nouveau mot de passe
            <input v-model="dashboardApp.resetPasswordForm.new_password" type="password" />
          </label>
          <label class="checkbox">
            <input v-model="dashboardApp.resetPasswordForm.must_change_password" type="checkbox" />
            Forcer changement
          </label>
          <button type="submit" class="btn-primary">Reset</button>
          <p v-if="userResetSuccess" class="feedback-success">{{ userResetSuccess }}</p>
          <p v-if="userResetError" class="feedback-error">{{ userResetError }}</p>
        </form>
      </div>

      <div class="list">
        <h3>Utilisateurs existants</h3>
        <p v-if="userRoleSuccess" class="feedback-success users-table-feedback">{{ userRoleSuccess }}</p>
        <p v-if="userRoleError" class="feedback-error users-table-feedback">{{ userRoleError }}</p>
        <div class="users-table-wrap">
          <table class="users-table">
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Rôle</th>
                <th>État</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in dashboardApp.users" :key="u.username">
                <td>{{ u.username }}</td>
                <td>
                  <select
                    class="role-select"
                    :value="u.role"
                    @change="onUserRoleChange(u, $event)"
                  >
                    <option v-for="r in allowedRoles" :key="r" :value="r">
                      {{ r }}
                    </option>
                  </select>
                </td>
                <td class="user-state">
                  <span v-if="u.must_change_password">mdp à changer</span>
                  <span v-else class="text-slate-400">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-if="dashboardApp.user?.role === 'admin'" class="card">
      <h2>Contenus Vellucast</h2>
      <button type="button" class="btn-primary" @click="dashboardApp.showUploadModal = true">
        Ajouter un média
      </button>
      <form class="create-content-form" @submit.prevent="submitCreateContent">
        <h3>Créer un contenu</h3>

        <div class="media-kind-tabs" role="tablist">
          <label class="media-kind-option">
            <input
              v-model="dashboardApp.contentForm.media_kind"
              type="radio"
              value="movie"
            />
            Film
          </label>
          <label class="media-kind-option">
            <input
              v-model="dashboardApp.contentForm.media_kind"
              type="radio"
              value="series"
            />
            Série
          </label>
        </div>

        <label>
          Identifiant (court)
          <input
            v-model="dashboardApp.contentForm.id"
            type="text"
            readonly
            class="input-readonly"
            autocomplete="off"
          />
          <p v-if="createErrors.id" class="field-error">{{ createErrors.id }}</p>
        </label>

        <label>
          Fichier sur le serveur
          <div class="path-row">
            <input
              :value="dashboardApp.contentForm.media_path || '(aucun fichier sélectionné)'"
              type="text"
              readonly
              class="input-readonly path-input"
            />
            <button type="button" class="btn-outline shrink-0" @click="showBrowseModal = true">
              Parcourir le serveur
            </button>
          </div>
          <p v-if="createErrors.media_path" class="field-error">{{ createErrors.media_path }}</p>
        </label>

        <label>
          Titre
          <input v-model="dashboardApp.contentForm.title" type="text" autocomplete="off" />
          <p v-if="createErrors.title" class="field-error">{{ createErrors.title }}</p>
        </label>

        <div v-if="dashboardApp.contentForm.media_kind === 'series'" class="series-fields">
          <label>
            Nom de la série
            <input v-model="dashboardApp.contentForm.series_name" type="text" autocomplete="off" />
            <p v-if="createErrors.series_name" class="field-error">{{ createErrors.series_name }}</p>
          </label>
          <div class="series-grid">
            <label>
              Saison
              <input
                v-model.number="dashboardApp.contentForm.season_number"
                type="number"
                min="1"
                step="1"
              />
              <p v-if="createErrors.season" class="field-error">{{ createErrors.season }}</p>
            </label>
            <label>
              Épisode
              <input
                v-model.number="dashboardApp.contentForm.episode_number"
                type="number"
                min="1"
                step="1"
              />
              <p v-if="createErrors.episode" class="field-error">{{ createErrors.episode }}</p>
            </label>
          </div>
        </div>

        <button type="submit" class="btn-primary">Créer</button>
        <p v-if="successMsgCreateContent" class="feedback-success">{{ successMsgCreateContent }}</p>
      </form>

      <ServerBrowseModal
        v-if="showBrowseModal"
        :token="dashboardApp.token"
        @close="showBrowseModal = false"
        @select="onBrowseSelect"
      />

      <form class="update-content-form muted" @submit.prevent="submitUpdateContent">
        <h3>Mettre à jour un contenu</h3>

        <div class="content-search-wrap">
          <label>
            Rechercher un contenu
            <input
              v-model="updateSearchQuery"
              type="search"
              autocomplete="off"
              placeholder="Tapez un titre ou un identifiant…"
              @focus="onUpdateSearchFocus"
              @blur="onUpdateSearchBlur"
            />
          </label>
          <ul
            v-if="showUpdateSuggestions"
            class="content-search-dropdown"
            role="listbox"
            aria-label="Résultats de recherche"
          >
            <li
              v-for="c in filteredContentsForUpdate"
              :key="c.id"
              role="option"
              class="content-search-item"
              @mousedown.prevent="selectContentForUpdate(c)"
            >
              <span class="content-search-title">{{ c.title }}</span>
              <span class="content-search-id">{{ c.id }}</span>
            </li>
          </ul>
          <p v-if="showUpdateNoResults" class="content-search-hint">
            Aucun contenu ne correspond à cette recherche.
          </p>
        </div>
        <p v-if="updateErrors.selection" class="field-error">{{ updateErrors.selection }}</p>

        <p v-if="dashboardApp.contentUpdateForm.id" class="update-selection-pill">
          <span class="update-selection-label">Sélection :</span>
          <strong>{{ dashboardApp.contentUpdateForm.title }}</strong>
          <span class="meta">({{ dashboardApp.contentUpdateForm.id }})</span>
          <button type="button" class="ghost text-sm shrink-0" @click="clearUpdateSelection">
            Changer
          </button>
        </p>

        <label>
          Nouveau titre
          <input
            v-model="dashboardApp.contentUpdateForm.title"
            type="text"
            autocomplete="off"
          />
          <p v-if="updateErrors.title" class="field-error">{{ updateErrors.title }}</p>
        </label>
        <label>
          Nouveau chemin
          <input v-model="dashboardApp.contentUpdateForm.media_path" type="text" />
        </label>
        <button type="submit" class="btn-primary">Mettre à jour</button>
        <p v-if="successMsgUpdateContent" class="feedback-success">{{ successMsgUpdateContent }}</p>
      </form>

      <div class="existing-contents-block">
        <h3 class="existing-contents-title">Contenus existants</h3>

        <div class="content-library-tabs" role="tablist" aria-label="Type de contenu">
          <button
            type="button"
            role="tab"
            class="content-tab-btn"
            :class="{ 'content-tab-btn--active': existingContentsTab === 'movies' }"
            :aria-selected="existingContentsTab === 'movies'"
            @click="existingContentsTab = 'movies'"
          >
            🎬 Films
          </button>
          <button
            type="button"
            role="tab"
            class="content-tab-btn"
            :class="{ 'content-tab-btn--active': existingContentsTab === 'series' }"
            :aria-selected="existingContentsTab === 'series'"
            @click="existingContentsTab = 'series'"
          >
            📺 Séries
          </button>
        </div>

        <!-- Vue Films -->
        <div
          v-show="existingContentsTab === 'movies'"
          class="content-tab-panel"
          role="tabpanel"
        >
          <p v-if="movieContents.length === 0" class="content-empty-hint">
            Aucun film. Les médias dont le titre suit le format « série - Saison n - … » sont
            classés sous l’onglet Séries.
          </p>
          <details
            v-for="c in movieContents"
            :key="c.id"
            class="content-accordion-card"
            @contextmenu.prevent.stop="openMediaCtx($event, c)"
          >
            <summary class="content-accordion-summary">{{ c.title }}</summary>
            <div class="content-accordion-body">
              <dl class="content-meta-dl">
                <div class="content-meta-row">
                  <dt>ID</dt>
                  <dd>
                    <code class="content-meta-code">{{ c.id }}</code>
                  </dd>
                </div>
                <div class="content-meta-row">
                  <dt>Chemin</dt>
                  <dd class="content-meta-path">{{ c.media_path }}</dd>
                </div>
                <div class="content-meta-row">
                  <dt>Date d'ajout</dt>
                  <dd>{{ formatContentDate(c.created_at) }}</dd>
                </div>
              </dl>
              <div class="content-accordion-actions">
                <button
                  type="button"
                  class="ghost content-delete-btn"
                  @click.stop="dashboardApp.deleteContent(c.id)"
                >
                  Supprimer
                </button>
              </div>
            </div>
          </details>
        </div>

        <!-- Vue Séries -->
        <div
          v-show="existingContentsTab === 'series'"
          class="content-tab-panel"
          role="tabpanel"
        >
          <p v-if="sortedSeriesNames.length === 0" class="content-empty-hint">
            Aucune série détectée. Les épisodes doivent avoir un titre du type « Nom de la
            série - Saison n - … » (comme à la création ou à l'upload).
          </p>

          <details
            v-for="seriesName in sortedSeriesNames"
            :key="seriesName"
            class="content-accordion-card content-accordion-card--series"
          >
            <summary class="content-accordion-summary content-accordion-summary--series">
              {{ seriesName }}
            </summary>
            <div class="series-episodes-stack">
              <template v-for="season in sortedSeasonsFor(seriesName)" :key="season">
                <div class="season-block">
                  <h4 class="season-block-title">Saison {{ season }}</h4>
                  <details
                    v-for="item in sortedEpisodesFor(seriesName, season)"
                    :key="item.content.id"
                    class="content-accordion-card content-accordion-card--nested"
                    @contextmenu.prevent.stop="openMediaCtx($event, item.content)"
                  >
                    <summary class="content-accordion-summary content-accordion-summary--episode">
                      {{ episodeSummaryLine(item) }}
                    </summary>
                    <div class="content-accordion-body">
                      <p class="content-full-title">{{ item.content.title }}</p>
                      <dl class="content-meta-dl">
                        <div class="content-meta-row">
                          <dt>ID</dt>
                          <dd>
                            <code class="content-meta-code">{{ item.content.id }}</code>
                          </dd>
                        </div>
                        <div class="content-meta-row">
                          <dt>Chemin</dt>
                          <dd class="content-meta-path">{{ item.content.media_path }}</dd>
                        </div>
                        <div class="content-meta-row">
                          <dt>Date d'ajout</dt>
                          <dd>{{ formatContentDate(item.content.created_at) }}</dd>
                        </div>
                      </dl>
                      <div class="content-accordion-actions">
                        <button
                          type="button"
                          class="ghost content-delete-btn"
                          @click.stop="dashboardApp.deleteContent(item.content.id)"
                        >
                          Supprimer
                        </button>
                      </div>
                    </div>
                  </details>
                </div>
              </template>
            </div>
          </details>
        </div>
      </div>
    </section>

    <MediaContextMenu
      :visible="mediaCtxOpen"
      :x="mediaCtxX"
      :y="mediaCtxY"
      :content="mediaCtxContent"
      :show-do-not-optimize="true"
      @close="closeMediaCtx"
      @action="onMediaCtxAction"
    />

    <div v-if="toastMessage" class="settings-toast" role="status">
      {{ toastMessage }}
    </div>

    <section v-if="dashboardApp.user?.role === 'admin'" class="card">
      <h2>Liens temporaires Vellucast</h2>
      <form @submit.prevent="submitCreateShare">
        <div class="content-search-wrap content-search-wrap--share">
          <label>
            Contenu cible (recherche par titre ou ID)
            <input
              v-model="shareSearchQuery"
              type="search"
              autocomplete="off"
              placeholder="Tapez le nom d'un film, une série ou un ID…"
              @focus="onShareSearchFocus"
              @blur="onShareSearchBlur"
            />
          </label>
          <ul
            v-if="showShareSuggestions"
            class="content-search-dropdown"
            role="listbox"
            aria-label="Contenus correspondants"
          >
            <li
              v-for="c in filteredContentsForShare"
              :key="c.id"
              role="option"
              class="content-search-item"
              @mousedown.prevent="selectContentForShare(c)"
            >
              <span class="content-search-title">{{ c.title }}</span>
              <span class="content-search-id">{{ c.id }}</span>
            </li>
          </ul>
          <p v-if="showShareNoResults" class="content-search-hint">
            Aucun contenu ne correspond à cette recherche.
          </p>
        </div>
        <p v-if="dashboardApp.shareForm.content_id" class="share-selection-pill">
          <span class="share-selection-label">ID sélectionné :</span>
          <code class="share-selection-id">{{ dashboardApp.shareForm.content_id }}</code>
          <button type="button" class="ghost text-sm shrink-0" @click="clearShareContentSelection">
            Effacer
          </button>
        </p>
        <label>
          Durée
          <div class="duration-row">
            <input v-model.number="dashboardApp.shareForm.expires_in_value" type="number" min="0" />
            <select v-model="dashboardApp.shareForm.expires_in_unit">
              <option value="minutes">Minutes</option>
              <option value="hours">Heures</option>
              <option value="days">Jours</option>
              <option value="weeks">Semaines</option>
              <option value="months">Mois (30j)</option>
              <option value="years">Années (365j)</option>
            </select>
          </div>
        </label>
        <label>
          Max usages
          <input v-model.number="dashboardApp.shareForm.max_uses" type="number" />
        </label>
        <label>
          Code d'accès
          <input v-model="dashboardApp.shareForm.access_code" type="text" />
        </label>
        <button type="submit" class="btn-primary">Créer le token</button>
        <p v-if="shareFormSuccess" class="feedback-success">{{ shareFormSuccess }}</p>
        <p v-if="shareFormError" class="feedback-error">{{ shareFormError }}</p>
      </form>

      <div v-if="dashboardApp.lastShareToken" class="token-box">
        <p>Token généré :</p>
        <div class="token-row">
          <code>{{ dashboardApp.lastShareToken }}</code>
          <button type="button" class="ghost" @click="dashboardApp.copyToken(dashboardApp.lastShareToken)">
            Copier
          </button>
        </div>
      </div>

      <div class="token-lists">
        <div class="token-section token-section--active">
          <h3 class="token-section-title">Tokens actifs</h3>
          <p v-if="activeShares.length === 0" class="token-empty-hint">
            Aucun token actif pour le moment.
          </p>
          <div v-else class="token-accordion-list">
            <details v-for="s in activeShares" :key="s.token" class="token-accordion-card">
              <summary class="token-accordion-summary">
                <span class="token-sum-content-id">{{ s.content_id }}</span>
                <span class="token-sum-token">{{ truncateTokenForSummary(s.token) }}</span>
              </summary>
              <div class="token-accordion-body">
                <dl class="token-detail-dl">
                  <div class="token-detail-row">
                    <dt>Jeton complet</dt>
                    <dd>
                      <code class="token-snippet token-snippet--full">{{ s.token }}</code>
                    </dd>
                  </div>
                  <div class="token-detail-row">
                    <dt>Usages</dt>
                    <dd>{{ s.used_count }}/{{ s.max_uses ?? "∞" }}</dd>
                  </div>
                  <div class="token-detail-row">
                    <dt>Expiration</dt>
                    <dd>
                      <template v-if="s.expires_at">
                        {{ formatShareExpiry(s.expires_at) }}
                      </template>
                      <template v-else>Pas d'expiration</template>
                    </dd>
                  </div>
                  <div v-if="s.requires_code" class="token-detail-row">
                    <dt>Accès</dt>
                    <dd><span class="token-badge-code">Code requis</span></dd>
                  </div>
                </dl>
                <div class="token-accordion-actions">
                  <button
                    type="button"
                    class="ghost token-action-btn"
                    @click.stop="onRevokeShareToken(s.token)"
                  >
                    Révoquer
                  </button>
                </div>
              </div>
            </details>
          </div>
        </div>

        <div class="token-section token-section--inactive">
          <h3 class="token-section-title">Tokens expirés ou inactifs</h3>
          <p class="token-section-help">
            Liens dont la date de fin est dépassée ou dont le nombre max d'usages est atteint. La
            révocation manuelle supprime l'entrée : elle n'apparaît plus ici.
          </p>
          <p v-if="inactiveShares.length === 0" class="token-empty-hint token-empty-hint--muted">
            Aucun historique (tout est actif ou les entrées inactives ont été retirées).
          </p>
          <div v-else class="token-accordion-list">
            <details
              v-for="s in inactiveShares"
              :key="s.token"
              class="token-accordion-card token-accordion-card--inactive"
            >
              <summary class="token-accordion-summary token-accordion-summary--inactive">
                <span class="token-status-badge token-status-badge--inline">{{
                  shareInactiveReason(s)
                }}</span>
                <span class="token-sum-content-id">{{ s.content_id }}</span>
                <span class="token-sum-token">{{ truncateTokenForSummary(s.token) }}</span>
              </summary>
              <div class="token-accordion-body">
                <dl class="token-detail-dl">
                  <div class="token-detail-row">
                    <dt>Jeton complet</dt>
                    <dd>
                      <code class="token-snippet token-snippet--full">{{ s.token }}</code>
                    </dd>
                  </div>
                  <div class="token-detail-row">
                    <dt>Usages</dt>
                    <dd>{{ s.used_count }}/{{ s.max_uses ?? "∞" }}</dd>
                  </div>
                  <div class="token-detail-row">
                    <dt>Expiration</dt>
                    <dd>
                      <template v-if="s.expires_at">
                        {{ formatShareExpiry(s.expires_at) }}
                      </template>
                      <template v-else>—</template>
                    </dd>
                  </div>
                  <div v-if="s.requires_code" class="token-detail-row">
                    <dt>Accès</dt>
                    <dd><span class="token-badge-code">Code requis</span></dd>
                  </div>
                </dl>
                <div class="token-accordion-actions">
                  <button
                    type="button"
                    class="ghost token-action-btn token-action-btn--danger-muted"
                    @click.stop="onRemoveInactiveShare(s.token)"
                  >
                    Supprimer définitivement
                  </button>
                </div>
              </div>
            </details>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { API_BASE } from "../config.js";
import ServerBrowseModal from "./ServerBrowseModal.vue";
import MediaContextMenu from "./MediaContextMenu.vue";

/** Rôles autorisés côté interface (alignés sur le backend). */
const ALLOWED_ROLES = ["user", "admin"];

/**
 * Détecte un titre d'épisode (upload / formulaire série) : « Nom - Saison N - … »
 * optionnellement « Ép. M - » avant le libellé.
 */
function parseSeriesFromTitle(title) {
  const re =
    /^(.+?)\s*-\s*Saison\s+(\d+)\s*-\s*(?:Ép\.\s*(\d+)\s*-\s*)?(.+)$/i;
  const m = (title || "").trim().match(re);
  if (!m) return null;
  return {
    seriesName: m[1].trim(),
    season: parseInt(m[2], 10),
    episode: m[3] != null ? parseInt(m[3], 10) : null,
    remainder: (m[4] || "").trim(),
  };
}

export default {
  name: "Settings",
  components: { ServerBrowseModal, MediaContextMenu },
  inject: ["dashboardApp"],
  data() {
    return {
      allowedRoles: ALLOWED_ROLES,
      folderForm: {
        movies_folder: "",
        series_folder: "",
      },
      folderSaving: false,
      folderMessage: "",
      folderError: "",
      transcodeForm: {
        stream_transcode_enabled: false,
        stream_transcode_preset: 3,
        auto_optimize_enabled: false,
        ffmpeg_params: "",
        optimize_schedule_type: "upload",
        optimize_start_time: "02:00",
        optimize_end_time: "06:00",
      },
      transcodeSaving: false,
      transcodeMessage: "",
      transcodeError: "",
      showBrowseModal: false,
      createErrors: {},
      toastMessage: "",
      toastTimer: null,
      updateSearchQuery: "",
      updateDropdownOpen: false,
      updateBlurTimer: null,
      updateErrors: {},
      /** Onglet actif pour la liste des contenus : films | series */
      existingContentsTab: "movies",
      successMsgCreateContent: "",
      successMsgUpdateContent: "",
      shareFormSuccess: "",
      shareFormError: "",
      userCreateSuccess: "",
      userCreateError: "",
      userUpdateSuccess: "",
      userUpdateError: "",
      userResetSuccess: "",
      userResetError: "",
      userRoleSuccess: "",
      userRoleError: "",
      mediaCtxOpen: false,
      mediaCtxX: 0,
      mediaCtxY: 0,
      mediaCtxContent: null,
      shareSearchQuery: "",
      shareDropdownOpen: false,
      shareBlurTimer: null,
    };
  },
  computed: {
    transcodeQualityLabel() {
      const q = this.transcodeForm.stream_transcode_preset;
      const labels = {
        1: "Rapide (qualité basse)",
        2: "Plutôt rapide",
        3: "Équilibré",
        4: "Plutôt lent",
        5: "Lent (qualité maximale)",
      };
      return labels[q] || labels[3];
    },
    activeShares() {
      return (this.dashboardApp.shares || []).filter((s) => s.is_valid);
    },
    inactiveShares() {
      return (this.dashboardApp.shares || []).filter((s) => !s.is_valid);
    },
    movieContents() {
      const list = this.dashboardApp.contents || [];
      return list.filter((c) => !parseSeriesFromTitle(c.title));
    },
    seriesTree() {
      const tree = {};
      for (const c of this.dashboardApp.contents || []) {
        const p = parseSeriesFromTitle(c.title);
        if (!p) continue;
        const name = p.seriesName;
        if (!tree[name]) tree[name] = {};
        if (!tree[name][p.season]) tree[name][p.season] = [];
        tree[name][p.season].push({ ...p, content: c });
      }
      return tree;
    },
    sortedSeriesNames() {
      return Object.keys(this.seriesTree).sort((a, b) =>
        a.localeCompare(b, "fr", { sensitivity: "base" }),
      );
    },
    filteredContentsForUpdate() {
      const q = (this.updateSearchQuery || "").trim().toLowerCase();
      if (!q) return [];
      const list = this.dashboardApp.contents || [];
      return list.filter((c) => {
        const title = (c.title || "").toLowerCase();
        const id = (c.id || "").toLowerCase();
        return title.includes(q) || id.includes(q);
      });
    },
    showUpdateSuggestions() {
      return (
        this.updateDropdownOpen &&
        (this.updateSearchQuery || "").trim().length > 0 &&
        this.filteredContentsForUpdate.length > 0
      );
    },
    showUpdateNoResults() {
      return (
        this.updateDropdownOpen &&
        (this.updateSearchQuery || "").trim().length > 0 &&
        this.filteredContentsForUpdate.length === 0
      );
    },
    filteredContentsForShare() {
      const q = (this.shareSearchQuery || "").trim().toLowerCase();
      if (!q) return [];
      const list = this.dashboardApp.contents || [];
      return list.filter((c) => {
        const title = (c.title || "").toLowerCase();
        const id = (c.id || "").toLowerCase();
        return title.includes(q) || id.includes(q);
      });
    },
    showShareSuggestions() {
      return (
        this.shareDropdownOpen &&
        (this.shareSearchQuery || "").trim().length > 0 &&
        this.filteredContentsForShare.length > 0
      );
    },
    showShareNoResults() {
      return (
        this.shareDropdownOpen &&
        (this.shareSearchQuery || "").trim().length > 0 &&
        this.filteredContentsForShare.length === 0
      );
    },
  },
  async mounted() {
    await this.loadFolderSettings();
    if (typeof this.dashboardApp.resetContentCreateForm === "function") {
      this.dashboardApp.resetContentCreateForm();
    }
  },
  beforeUnmount() {
    if (this.toastTimer) clearTimeout(this.toastTimer);
    if (this.updateBlurTimer) clearTimeout(this.updateBlurTimer);
    if (this.shareBlurTimer) clearTimeout(this.shareBlurTimer);
  },
  methods: {
    sortedSeasonsFor(seriesName) {
      return Object.keys(this.seriesTree[seriesName] || {})
        .map(Number)
        .sort((a, b) => a - b);
    },
    sortedEpisodesFor(seriesName, season) {
      const arr = [...(this.seriesTree[seriesName]?.[season] || [])];
      return arr.sort((a, b) => {
        if (a.episode != null && b.episode != null) {
          return a.episode - b.episode;
        }
        if (a.episode != null) return -1;
        if (b.episode != null) return 1;
        return (a.content.title || "").localeCompare(b.content.title || "", "fr");
      });
    },
    formatContentDate(iso) {
      if (!iso) return "—";
      try {
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleString("fr-FR", {
          dateStyle: "medium",
          timeStyle: "short",
        });
      } catch {
        return iso;
      }
    },
    episodeSummaryLine(item) {
      if (item.episode != null) {
        return `Ép. ${item.episode} — ${item.remainder || item.content.title}`;
      }
      return item.remainder || item.content.title;
    },
    clearCreateErrors() {
      this.createErrors = {};
    },
    validateCreateForm() {
      const e = {};
      const f = this.dashboardApp.contentForm;
      if (!(f.id || "").trim()) {
        e.id = "L'identifiant est requis.";
      }
      if (!(f.media_path || "").trim()) {
        e.media_path = "Sélectionnez un fichier vidéo sur le serveur.";
      }
      if (!(f.title || "").trim()) {
        e.title = "Le titre ne peut pas être vide.";
      }
      if (f.media_kind === "series") {
        if (!(f.series_name || "").trim()) {
          e.series_name = "Le nom de la série est requis.";
        }
        const s = Number(f.season_number);
        const ep = Number(f.episode_number);
        if (!Number.isFinite(s) || s < 1) {
          e.season = "Indiquez un numéro de saison (≥ 1).";
        }
        if (!Number.isFinite(ep) || ep < 1) {
          e.episode = "Indiquez un numéro d'épisode (≥ 1).";
        }
      }
      this.createErrors = e;
      return Object.keys(e).length === 0;
    },
    showToast(msg) {
      this.toastMessage = msg;
      if (this.toastTimer) {
        clearTimeout(this.toastTimer);
      }
      this.toastTimer = setTimeout(() => {
        this.toastMessage = "";
      }, 4500);
    },
    async submitCreateContent() {
      this.successMsgCreateContent = "";
      this.clearCreateErrors();
      if (!this.validateCreateForm()) {
        this.showToast("Veuillez corriger les champs en erreur.");
        return;
      }
      const res = await this.dashboardApp.createContent();
      if (res && res.ok === false) {
        this.showToast(
          typeof res.detail === "string"
            ? res.detail
            : "Échec de la création du contenu.",
        );
      } else if (res && res.ok) {
        this.successMsgCreateContent = "Contenu créé avec succès.";
      }
    },
    onBrowseSelect({ path, name }) {
      this.dashboardApp.contentForm.media_path = path;
      const stem = name.includes(".") ? name.slice(0, name.lastIndexOf(".")) : name;
      this.dashboardApp.contentForm.title = stem
        .replace(/_/g, " ")
        .replace(/\./g, " ")
        .trim() || "Sans titre";
    },
    clearUpdateErrors() {
      this.updateErrors = {};
    },
    validateUpdateForm() {
      const e = {};
      const f = this.dashboardApp.contentUpdateForm;
      if (!(f.id || "").trim()) {
        e.selection =
          "Sélectionnez un contenu dans la liste déroulante (résultats de recherche).";
      }
      if (!(f.title || "").trim()) {
        e.title = "Le titre ne peut pas être vide.";
      }
      this.updateErrors = e;
      return Object.keys(e).length === 0;
    },
    onUpdateSearchFocus() {
      if (this.updateBlurTimer) {
        clearTimeout(this.updateBlurTimer);
        this.updateBlurTimer = null;
      }
      this.updateDropdownOpen = true;
    },
    onUpdateSearchBlur() {
      this.updateBlurTimer = setTimeout(() => {
        this.updateDropdownOpen = false;
      }, 200);
    },
    selectContentForUpdate(c) {
      this.dashboardApp.contentUpdateForm.id = c.id;
      this.dashboardApp.contentUpdateForm.title = c.title || "";
      this.dashboardApp.contentUpdateForm.media_path = c.media_path || "";
      this.updateSearchQuery = "";
      this.updateDropdownOpen = false;
      this.clearUpdateErrors();
    },
    clearUpdateSelection() {
      this.updateSearchQuery = "";
      this.dashboardApp.contentUpdateForm.id = "";
      this.dashboardApp.contentUpdateForm.title = "";
      this.dashboardApp.contentUpdateForm.media_path = "";
      this.clearUpdateErrors();
    },
    async submitUpdateContent() {
      this.successMsgUpdateContent = "";
      this.clearUpdateErrors();
      if (!this.validateUpdateForm()) {
        const first =
          this.updateErrors.selection || this.updateErrors.title || "";
        this.showToast(first || "Veuillez corriger le formulaire.");
        return;
      }
      const res = await this.dashboardApp.updateContent();
      if (res && res.ok === false) {
        this.showToast(
          typeof res.detail === "string"
            ? res.detail
            : "Échec de la mise à jour du contenu.",
        );
      } else if (res && res.ok) {
        this.successMsgUpdateContent = "Contenu mis à jour avec succès.";
      }
    },
    async submitCreateUser() {
      this.userCreateSuccess = "";
      this.userCreateError = "";
      const res = await this.dashboardApp.createUser();
      if (res?.ok) {
        this.userCreateSuccess = "Utilisateur créé avec succès.";
      } else {
        this.userCreateError = res?.detail || "Échec de la création.";
      }
    },
    async submitUpdateUser() {
      this.userUpdateSuccess = "";
      this.userUpdateError = "";
      const res = await this.dashboardApp.updateUser();
      if (res?.ok) {
        this.userUpdateSuccess = "Utilisateur mis à jour avec succès.";
      } else {
        this.userUpdateError = res?.detail || "Échec de la mise à jour.";
      }
    },
    async submitResetUserPassword() {
      this.userResetSuccess = "";
      this.userResetError = "";
      const res = await this.dashboardApp.resetUserPassword();
      if (res?.ok) {
        this.userResetSuccess = "Mot de passe réinitialisé avec succès.";
      } else {
        this.userResetError = res?.detail || "Échec de la réinitialisation.";
      }
    },
    async onUserRoleChange(userRow, event) {
      const newRole = event.target.value;
      this.userRoleSuccess = "";
      this.userRoleError = "";
      const res = await this.dashboardApp.updateUserRoleFromList(userRow, newRole);
      if (res?.skipped) return;
      if (res?.ok) {
        this.userRoleSuccess = "Rôle mis à jour.";
      } else {
        this.userRoleError = res?.detail || "Impossible de modifier le rôle.";
        await this.dashboardApp.loadUsers();
      }
    },
    async submitCreateShare() {
      this.shareFormError = "";
      this.shareFormSuccess = "";
      if (!(this.dashboardApp.shareForm.content_id || "").trim()) {
        this.shareFormError =
          "Sélectionnez un contenu dans la liste de résultats (recherche par titre ou ID).";
        return;
      }
      const res = await this.dashboardApp.createShare();
      if (res?.ok) {
        this.shareFormSuccess = "Token créé avec succès.";
      } else {
        this.shareFormError = res?.detail || "Échec de la création du token.";
      }
    },
    onShareSearchFocus() {
      if (this.shareBlurTimer) {
        clearTimeout(this.shareBlurTimer);
        this.shareBlurTimer = null;
      }
      this.shareDropdownOpen = true;
    },
    onShareSearchBlur() {
      this.shareBlurTimer = setTimeout(() => {
        this.shareDropdownOpen = false;
      }, 200);
    },
    selectContentForShare(c) {
      this.dashboardApp.shareForm.content_id = c.id;
      this.shareSearchQuery = "";
      this.shareDropdownOpen = false;
      this.shareFormError = "";
    },
    clearShareContentSelection() {
      this.dashboardApp.shareForm.content_id = "";
      this.shareSearchQuery = "";
      this.shareFormError = "";
    },
    truncateTokenForSummary(token) {
      const t = token || "";
      if (t.length <= 32) return t;
      return `${t.slice(0, 14)}…${t.slice(-12)}`;
    },
    shareInactiveReason(s) {
      const exp = s.expires_at;
      if (exp) {
        const t = Date.parse(exp);
        if (!Number.isNaN(t) && t < Date.now()) {
          return "Expiré";
        }
      }
      const max = s.max_uses;
      if (max != null && (s.used_count || 0) >= max) {
        return "Quota atteint";
      }
      return "Inactif";
    },
    formatShareExpiry(iso) {
      if (!iso) return "";
      try {
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleString("fr-FR", {
          dateStyle: "medium",
          timeStyle: "short",
        });
      } catch {
        return iso;
      }
    },
    async onRevokeShareToken(token) {
      this.shareFormError = "";
      const res = await this.dashboardApp.revokeShare(token);
      if (res?.ok) {
        this.shareFormSuccess = "Token révoqué.";
        setTimeout(() => {
          this.shareFormSuccess = "";
        }, 4500);
      } else {
        this.showToast(res?.detail || "Échec de la révocation.");
      }
    },
    async onRemoveInactiveShare(token) {
      this.shareFormError = "";
      const res = await this.dashboardApp.revokeShare(token);
      if (res?.ok) {
        this.shareFormSuccess = "Entrée supprimée définitivement.";
        setTimeout(() => {
          this.shareFormSuccess = "";
        }, 4500);
      } else {
        this.showToast(res?.detail || "Échec de la suppression.");
      }
    },
    openMediaCtx(event, content) {
      this.mediaCtxX = event.clientX;
      this.mediaCtxY = event.clientY;
      this.mediaCtxContent = content;
      this.mediaCtxOpen = true;
    },
    closeMediaCtx() {
      this.mediaCtxOpen = false;
      this.mediaCtxContent = null;
    },
    onMediaCtxAction({ type, content }) {
      if (type === "no_optimize") {
        this.toggleDoNotOptimizeContent(content);
        return;
      }
      console.log(`[Vellucast contexte] ${type}`, { id: content?.id, content });
    },
    async toggleDoNotOptimizeContent(content) {
      if (!content?.id) return;
      try {
        const response = await fetch(
          `${API_BASE}/api/contents/${encodeURIComponent(content.id)}/toggle-optimize`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${this.dashboardApp.token}`,
            },
          },
        );
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.showToast(
            typeof data.detail === "string"
              ? data.detail
              : "Impossible de mettre à jour l'option d'optimisation.",
          );
          return;
        }
        const nextFlag =
          data && Object.prototype.hasOwnProperty.call(data, "do_not_optimize")
            ? Boolean(data.do_not_optimize)
            : !Boolean(content.do_not_optimize);
        if (typeof this.dashboardApp.applyContentDoNotOptimizeToggle === "function") {
          this.dashboardApp.applyContentDoNotOptimizeToggle(content.id, nextFlag);
        } else if (typeof this.dashboardApp.loadContents === "function") {
          await this.dashboardApp.loadContents();
        }
      } catch (e) {
        console.error("[do_not_optimize]", e);
        this.showToast("Erreur réseau.");
      }
    },
    applySettingsFromApi(data) {
      if (!data || typeof data !== "object") return;
      if (data.movies_folder !== undefined) {
        this.folderForm.movies_folder = data.movies_folder || "";
      }
      if (data.series_folder !== undefined) {
        this.folderForm.series_folder = data.series_folder || "";
      }
      const tf = this.transcodeForm;
      const streamOn =
        data.stream_transcode_enabled !== undefined
          ? data.stream_transcode_enabled
          : data.transcode_stream_enabled;
      if (streamOn !== undefined) {
        tf.stream_transcode_enabled =
          streamOn === true || streamOn === "1" || streamOn === 1;
      }
      const presetRaw =
        data.stream_transcode_preset !== undefined
          ? data.stream_transcode_preset
          : data.transcode_stream_quality;
      if (presetRaw !== undefined) {
        const q = parseInt(String(presetRaw), 10);
        tf.stream_transcode_preset = Number.isFinite(q)
          ? Math.min(5, Math.max(1, q))
          : 3;
      }
      if (data.auto_optimize_enabled !== undefined) {
        tf.auto_optimize_enabled =
          data.auto_optimize_enabled === true ||
          data.auto_optimize_enabled === "1" ||
          data.auto_optimize_enabled === 1;
      }
      const ffmpeg =
        data.ffmpeg_params !== undefined
          ? data.ffmpeg_params
          : data.auto_optimize_ffmpeg_args;
      if (ffmpeg !== undefined) {
        tf.ffmpeg_params = ffmpeg || "";
      }
      const schedType =
        data.optimize_schedule_type !== undefined
          ? data.optimize_schedule_type
          : data.auto_optimize_trigger;
      if (schedType !== undefined) {
        const tr = String(schedType || "").toLowerCase();
        tf.optimize_schedule_type =
          tr === "scheduled" ? "scheduled" : "upload";
      }
      const tStart =
        data.optimize_start_time !== undefined
          ? data.optimize_start_time
          : data.auto_optimize_schedule_start;
      if (tStart !== undefined) {
        tf.optimize_start_time = tStart || "02:00";
      }
      const tEnd =
        data.optimize_end_time !== undefined
          ? data.optimize_end_time
          : data.auto_optimize_schedule_end;
      if (tEnd !== undefined) {
        tf.optimize_end_time = tEnd || "06:00";
      }
    },
    async loadFolderSettings() {
      this.folderError = "";
      this.folderMessage = "";
      try {
        const response = await fetch(`${API_BASE}/api/settings`, {
          headers: { Authorization: `Bearer ${this.dashboardApp.token}` },
        });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          this.folderError = body.detail || `Erreur ${response.status}`;
          return;
        }
        const data = await response.json();
        this.applySettingsFromApi(data);
      } catch (e) {
        this.folderError = "Impossible de charger la configuration.";
      }
    },
    async saveFolderSettings() {
      this.folderSaving = true;
      this.folderError = "";
      this.folderMessage = "";
      try {
        const response = await fetch(`${API_BASE}/api/settings`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.dashboardApp.token}`,
          },
          body: JSON.stringify({
            movies_folder: this.folderForm.movies_folder,
            series_folder: this.folderForm.series_folder,
          }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.folderError = data.detail || data.error || `Erreur ${response.status}`;
          return;
        }
        this.folderMessage = "Configuration enregistrée.";
        this.applySettingsFromApi(data);
      } catch (e) {
        this.folderError = "Échec de l'enregistrement.";
      } finally {
        this.folderSaving = false;
      }
    },
    async saveTranscodingSettings() {
      this.transcodeSaving = true;
      this.transcodeMessage = "";
      this.transcodeError = "";
      try {
        const response = await fetch(`${API_BASE}/api/settings`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${this.dashboardApp.token}`,
          },
          body: JSON.stringify({
            stream_transcode_enabled: this.transcodeForm.stream_transcode_enabled,
            stream_transcode_preset: this.transcodeForm.stream_transcode_preset,
            auto_optimize_enabled: this.transcodeForm.auto_optimize_enabled,
            ffmpeg_params: this.transcodeForm.ffmpeg_params,
            optimize_schedule_type: this.transcodeForm.optimize_schedule_type,
            optimize_start_time: this.transcodeForm.optimize_start_time,
            optimize_end_time: this.transcodeForm.optimize_end_time,
          }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          this.transcodeError =
            data.detail || data.error || `Erreur ${response.status}`;
          return;
        }
        this.transcodeMessage = "Paramètres de transcodage enregistrés.";
        this.applySettingsFromApi(data);
      } catch (e) {
        this.transcodeError = "Échec de l'enregistrement.";
      } finally {
        this.transcodeSaving = false;
      }
    },
  },
};
</script>

<style scoped>
/* Aligné sur les champs input du dashboard (bordures, padding, police). */
.role-select {
  width: 100%;
  min-width: 8rem;
  max-width: 14rem;
  padding: 0.6rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.95rem;
  background: #fff;
  color: #1f2937;
}

.users-table-wrap {
  overflow-x: auto;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

.users-table th,
.users-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.users-table th {
  color: #374151;
  font-weight: 600;
}

.user-state {
  color: #6b7280;
  font-size: 0.9rem;
}

.create-content-form h3 {
  margin-bottom: 0.75rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
}

.media-kind-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.media-kind-option {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #334155;
}

.path-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
  flex-wrap: wrap;
}

.path-input {
  flex: 1;
  min-width: 12rem;
}

.input-readonly {
  background: #f1f5f9 !important;
  color: #475569 !important;
  cursor: default;
}

.series-fields {
  display: grid;
  gap: 0.75rem;
  padding: 0.75rem 0;
}

.series-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.field-error {
  color: #b91c1c;
  font-size: 0.8rem;
  margin: 0.25rem 0 0;
}

.settings-toast {
  position: fixed;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 80;
  max-width: min(32rem, 92vw);
  padding: 0.75rem 1.25rem;
  border-radius: 10px;
  background: #1e293b;
  color: #f8fafc;
  font-size: 0.9rem;
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.35);
}

.update-content-form h3 {
  margin-bottom: 0.75rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
}

.content-search-wrap {
  position: relative;
  z-index: 2;
}

.content-search-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  margin-top: 0.25rem;
  max-height: 14rem;
  overflow-y: auto;
  list-style: none;
  padding: 0.25rem 0;
  margin-bottom: 0;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
}

.content-search-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 0.9rem;
  border-bottom: 1px solid #f1f5f9;
}

.content-search-item:last-child {
  border-bottom: none;
}

.content-search-item:hover {
  background: #f8fafc;
}

.content-search-title {
  font-weight: 500;
  color: #0f172a;
}

.content-search-id {
  font-size: 0.8rem;
  color: #64748b;
  font-family: ui-monospace, monospace;
}

.content-search-hint {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
}

.update-selection-pill {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
  margin: 0.5rem 0 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  background: #f1f5f9;
  font-size: 0.9rem;
  color: #334155;
}

.update-selection-label {
  color: #64748b;
}

.settings-page-title {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem 0.75rem;
}

.settings-brand {
  background: linear-gradient(135deg, #312e81 0%, #4f46e5 50%, #6d28d9 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.settings-page-sub {
  font-weight: 600;
  color: #64748b;
  font-size: 1.1rem;
}

.content-search-wrap--share {
  z-index: 3;
  margin-bottom: 0.25rem;
}

.share-selection-pill {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.5rem;
  margin: 0.5rem 0 1rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  background: #eef2ff;
  border: 1px solid #c7d2fe;
  font-size: 0.9rem;
  color: #334155;
}

.share-selection-label {
  color: #64748b;
}

.share-selection-id {
  font-size: 0.85rem;
  padding: 0.1rem 0.35rem;
  border-radius: 6px;
  background: #fff;
  color: #1e1b4b;
  font-family: ui-monospace, monospace;
}

/* --- Liste contenus existants (onglets Films / Séries) --- */
.existing-contents-block {
  margin-top: 1.75rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.existing-contents-title {
  margin: 0 0 1rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
}

.content-library-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.content-tab-btn {
  flex: 1;
  min-width: 10rem;
  padding: 0.85rem 1.25rem;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.content-tab-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.content-tab-btn--active {
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  border-color: #a5b4fc;
  color: #1e1b4b;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.15);
}

.content-tab-panel {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.content-empty-hint {
  margin: 0 0 0.5rem;
  padding: 1rem 1.1rem;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 0.9rem;
  line-height: 1.45;
}

.content-accordion-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.content-accordion-card--series {
  border-color: #c7d2fe;
  background: linear-gradient(180deg, #fafaff 0%, #fff 100%);
}

.content-accordion-card--nested {
  margin-left: 0.25rem;
  border-radius: 10px;
  border-color: #e2e8f0;
}

.content-accordion-card > summary {
  list-style: none;
  cursor: pointer;
  padding: 0.85rem 1rem;
  font-weight: 600;
  color: #1e293b;
  user-select: none;
}

.content-accordion-card > summary::-webkit-details-marker {
  display: none;
}

.content-accordion-summary {
  position: relative;
  padding-right: 1.75rem;
}

.content-accordion-summary::after {
  content: "▸";
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 0.85rem;
  transition: transform 0.2s ease;
}

.content-accordion-card[open] > .content-accordion-summary::after {
  transform: translateY(-50%) rotate(90deg);
}

.content-accordion-summary--series {
  font-size: 1.02rem;
  color: #312e81;
}

.content-accordion-summary--episode {
  font-weight: 500;
  font-size: 0.95rem;
}

.content-accordion-body {
  padding: 0 1rem 1rem;
  border-top: 1px solid #f1f5f9;
  background: #fafafa;
}

.content-meta-dl {
  margin: 0;
  padding: 0.75rem 0 0;
}

.content-meta-row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 0.35rem 0.75rem;
  align-items: start;
  margin-bottom: 0.5rem;
  font-size: 0.88rem;
}

.content-meta-row:last-child {
  margin-bottom: 0;
}

.content-meta-row dt {
  margin: 0;
  color: #64748b;
  font-weight: 500;
}

.content-meta-row dd {
  margin: 0;
  color: #1e293b;
  word-break: break-word;
}

.content-meta-code {
  font-size: 0.82rem;
  padding: 0.15rem 0.4rem;
  border-radius: 6px;
  background: #f1f5f9;
  color: #0f172a;
}

.content-meta-path {
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
  line-height: 1.4;
}

.content-accordion-actions {
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.content-delete-btn {
  border-radius: 8px;
  color: #b91c1c;
}

.content-delete-btn:hover {
  background: #fef2f2;
}

.series-episodes-stack {
  padding: 0 0.75rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.season-block {
  margin: 0;
}

.season-block-title {
  margin: 0 0 0.5rem;
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6366f1;
}

.content-full-title {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: #64748b;
  line-height: 1.4;
}

/* Retours formulaires (succès / erreur) */
.feedback-success {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: #047857;
}

.feedback-error {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: #b91c1c;
}

.transcoding-settings-card .transcoding-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
  color: #1e293b;
}

.transcoding-settings-card .transcoding-checkbox input {
  margin-top: 0.2rem;
}

.transcode-range {
  accent-color: #4f46e5;
}

.transcoding-radio {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-top: 0.35rem;
  cursor: pointer;
  font-size: 0.92rem;
  color: #334155;
}

.optimize-trigger-fieldset {
  border: none;
  padding: 0;
  margin: 0;
}

.schedule-times label {
  display: grid;
  gap: 0.35rem;
}

.users-table-feedback {
  margin-bottom: 0.5rem;
}

/* Sections tokens */
.token-lists {
  margin-top: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.token-section {
  padding: 1.1rem 1.15rem;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: #fafafa;
}

.token-section--active {
  border-color: #a5b4fc;
  background: linear-gradient(165deg, #f8fafc 0%, #fff 55%);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.08);
}

.token-section--inactive {
  border-color: #e2e8f0;
  background: #f8fafc;
}

.token-section-title {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: #0f172a;
}

.token-section-help {
  margin: 0 0 1rem;
  font-size: 0.82rem;
  line-height: 1.45;
  color: #64748b;
}

.token-empty-hint {
  margin: 0;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  background: #fff;
  border: 1px dashed #cbd5e1;
  color: #64748b;
  font-size: 0.9rem;
}

.token-empty-hint--muted {
  background: #f1f5f9;
  border-style: solid;
  border-color: #e2e8f0;
}

.token-accordion-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.token-accordion-card {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
  overflow: hidden;
}

.token-accordion-card--inactive {
  opacity: 0.92;
  background: #f8fafc;
  border-color: #e2e8f0;
}

.token-accordion-card > summary {
  list-style: none;
  cursor: pointer;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
  padding: 0.65rem 0.85rem;
  font-size: 0.88rem;
  user-select: none;
}

.token-accordion-card > summary::-webkit-details-marker {
  display: none;
}

.token-accordion-summary {
  position: relative;
  padding-right: 1.5rem;
}

.token-accordion-summary::after {
  content: "▸";
  position: absolute;
  right: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  font-size: 0.8rem;
  transition: transform 0.2s ease;
}

.token-accordion-card[open] > .token-accordion-summary::after {
  transform: translateY(-50%) rotate(90deg);
}

.token-sum-content-id {
  font-weight: 700;
  color: #0f172a;
}

.token-sum-token {
  font-family: ui-monospace, monospace;
  font-size: 0.78rem;
  color: #64748b;
  word-break: break-all;
  flex: 1;
  min-width: 8rem;
}

.token-accordion-summary--inactive .token-sum-content-id {
  color: #475569;
}

.token-status-badge--inline {
  margin: 0;
  flex-shrink: 0;
}

.token-accordion-body {
  padding: 0 0.85rem 0.85rem;
  border-top: 1px solid #f1f5f9;
  background: #fafafa;
}

.token-detail-dl {
  margin: 0;
  padding-top: 0.65rem;
}

.token-detail-row {
  display: grid;
  grid-template-columns: 7rem 1fr;
  gap: 0.35rem 0.65rem;
  margin-bottom: 0.45rem;
  font-size: 0.85rem;
  align-items: start;
}

.token-detail-row dt {
  margin: 0;
  color: #64748b;
  font-weight: 500;
}

.token-detail-row dd {
  margin: 0;
  color: #1e293b;
}

.token-snippet {
  display: block;
  font-size: 0.75rem;
  padding: 0.2rem 0.45rem;
  border-radius: 6px;
  background: #f1f5f9;
  color: #334155;
  word-break: break-all;
}

.token-snippet--full {
  font-size: 0.72rem;
}

.token-badge-code {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  background: #fef3c7;
  color: #92400e;
  font-size: 0.72rem;
  font-weight: 600;
}

.token-status-badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  background: #e2e8f0;
  color: #475569;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.token-accordion-actions {
  margin-top: 0.75rem;
  padding-top: 0.65rem;
  border-top: 1px solid #e2e8f0;
}

.token-action-btn {
  flex-shrink: 0;
}

.token-action-btn--danger-muted {
  color: #9ca3af;
  border-color: #d1d5db;
}

.token-action-btn--danger-muted:hover {
  color: #b91c1c;
  border-color: #fca5a5;
  background: #fef2f2;
}
</style>
