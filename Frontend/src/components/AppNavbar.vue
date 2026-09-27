<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  Activity,
  Users,
  Dna,
  ShieldCheck,
  BookOpen,
  LogOut,
  UserCheck,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const roleClass = computed(() => {
  switch (authStore.userRole) {
    case 'Administrator':
      return 'pm-badge-neutral'
    case 'Clinician':
      return 'pm-badge-info'
    case 'Lab_Officer':
      return 'pm-badge-warning'
    case 'Auditor':
      return 'pm-badge-success'
    default:
      return 'pm-badge-neutral'
  }
})

const handleLogout = async () => {
  await authStore.logout()
}
</script>

<template>
  <header class="pm-navbar">
    <div class="pm-navbar-container">
      <!-- Brand & Hospital Name -->
      <div class="pm-brand" @click="router.push('/')">
        <div class="pm-brand-icon">
          <Activity :size="20" />
        </div>
        <div class="pm-brand-text">
          <span class="pm-brand-title">PM-CDSS</span>
          <span class="pm-brand-subtitle">Levy Mwanawasa Teaching Hospital</span>
        </div>
      </div>

      <!-- Navigation Links (RBAC Gated) -->
      <nav class="pm-nav-links">
        <router-link
          v-if="authStore.canViewClinicalCharts"
          to="/"
          class="pm-nav-link"
          :class="{ active: route.path === '/' || route.path.startsWith('/patients') }"
        >
          <Users :size="16" />
          <span>Patients</span>
        </router-link>

        <router-link
          v-if="authStore.isLabOfficer || authStore.isAdmin"
          to="/lab-ingest"
          class="pm-nav-link"
          :class="{ active: route.path === '/lab-ingest' }"
        >
          <Dna :size="16" />
          <span>Lab Ingestion</span>
        </router-link>

        <router-link
          to="/rules"
          class="pm-nav-link"
          :class="{ active: route.path === '/rules' }"
        >
          <BookOpen :size="16" />
          <span>PGx Rules</span>
        </router-link>

        <router-link
          v-if="authStore.isAuditor || authStore.isAdmin"
          to="/audit"
          class="pm-nav-link"
          :class="{ active: route.path === '/audit' }"
        >
          <ShieldCheck :size="16" />
          <span>Audit Trail</span>
        </router-link>

        <router-link
          v-if="authStore.isAdmin"
          to="/users"
          class="pm-nav-link"
          :class="{ active: route.path === '/users' }"
        >
          <UserCheck :size="16" />
          <span>User Access</span>
        </router-link>
      </nav>

      <!-- Right User Session Info -->
      <div class="pm-user-panel">
        <div class="pm-user-meta">
          <span class="pm-user-name">{{ authStore.user?.full_name || 'Healthcare User' }}</span>
          <span class="pm-badge" :class="roleClass">{{ authStore.userRole }}</span>
        </div>
        <button
          type="button"
          class="pm-btn pm-btn-secondary pm-btn-sm"
          title="Sign out of clinical session"
          @click="handleLogout"
        >
          <LogOut :size="14" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.pm-navbar {
  background-color: var(--pm-bg-card);
  border-bottom: 1px solid var(--pm-border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.pm-navbar-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: var(--pm-header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.pm-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  user-select: none;
}

.pm-brand-icon {
  background-color: var(--pm-primary);
  color: #ffffff;
  width: 32px;
  height: 32px;
  border-radius: var(--pm-radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pm-brand-text {
  display: flex;
  flex-direction: column;
}

.pm-brand-title {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--pm-text-primary);
  line-height: 1.1;
}

.pm-brand-subtitle {
  font-size: 0.7rem;
  color: var(--pm-text-muted);
}

.pm-nav-links {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pm-nav-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.825rem;
  font-weight: 500;
  color: var(--pm-text-secondary);
  border-radius: var(--pm-radius);
  transition: all 0.15s ease;
  border: 1px solid transparent;
}

.pm-nav-link:hover {
  background-color: var(--pm-bg-subtle);
  color: var(--pm-text-primary);
}

.pm-nav-link.active {
  background-color: var(--pm-primary-light);
  color: var(--pm-primary);
  border-color: #bae6fd;
}

.pm-user-panel {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.pm-user-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pm-user-name {
  font-size: 0.825rem;
  font-weight: 500;
  color: var(--pm-text-primary);
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1024px) {
  .pm-brand-subtitle {
    display: none;
  }
  .pm-user-name {
    display: none;
  }
}
</style>
