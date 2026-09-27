<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { Activity, ShieldAlert, ArrowRight, CheckCircle2 } from 'lucide-vue-next'

const authStore = useAuthStore()

const email = ref('clinician@lmth.gov.zm')
const password = ref('ClinicianPass123!')

const presetRoles = [
  {
    role: 'Clinician',
    name: 'Dr. Chileshe Bwalya',
    email: 'clinician@lmth.gov.zm',
    pass: 'ClinicianPass123!',
    badge: 'pm-badge-info',
    desc: 'Patient charts, medication orders, CDSS alert review',
  },
  {
    role: 'Administrator',
    name: 'Dr. Mutale Mwila',
    email: 'admin@lmth.gov.zm',
    pass: 'AdminPass123!',
    badge: 'pm-badge-neutral',
    desc: 'System governance, rule authoring, user provisioning',
  },
  {
    role: 'Lab Officer',
    name: 'Kondwani Phiri',
    email: 'lab@lmth.gov.zm',
    pass: 'LabPass123!',
    badge: 'pm-badge-warning',
    desc: 'Genomic biomarker entry, sequencing validation',
  },
  {
    role: 'Auditor',
    name: 'Besa Musonda',
    email: 'auditor@lmth.gov.zm',
    pass: 'AuditorPass123!',
    badge: 'pm-badge-success',
    desc: 'Read-only compliance audit trail inspection',
  },
]

const selectRole = (item: typeof presetRoles[0]) => {
  email.value = item.email
  password.value = item.pass
}

const handleLogin = async () => {
  await authStore.login(email.value, password.value)
}
</script>

<template>
  <div class="pm-login-container">
    <div class="pm-login-card pm-card">
      <!-- Clinical Header -->
      <div class="pm-login-header">
        <div class="pm-login-icon">
          <Activity :size="28" />
        </div>
        <div>
          <h1 class="pm-login-title">PM-CDSS Login</h1>
          <p class="pm-login-sub">Personalized Medicine Decision Support</p>
          <p class="pm-login-inst">Levy Mwanawasa Teaching Hospital, Zambia</p>
        </div>
      </div>

      <!-- Institutional Directive Alert -->
      <div class="pm-alert-banner info" style="margin-bottom: 1.25rem;">
        <ShieldAlert :size="18" style="flex-shrink: 0; margin-top: 2px;" />
        <div style="font-size: 0.775rem; line-height: 1.4;">
          <strong>Clinical Safety Directive:</strong> This system is strictly an auxiliary decision-support tool.
          It does not autonomously diagnose or prescribe. Final responsibility remains with qualified healthcare personnel.
        </div>
      </div>

      <!-- Error Banner -->
      <div v-if="authStore.error" class="pm-alert-banner critical" style="margin-bottom: 1rem;">
        <ShieldAlert :size="18" style="flex-shrink: 0;" />
        <span style="font-size: 0.8rem;">{{ authStore.error }}</span>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="pm-login-form">
        <div class="pm-form-group">
          <label class="pm-form-label" for="login-email">Hospital Email / Username</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            required
            class="pm-input"
            placeholder="e.g. clinician@lmth.gov.zm"
          />
        </div>

        <div class="pm-form-group">
          <label class="pm-form-label" for="login-password">Password</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            required
            class="pm-input"
            placeholder="••••••••••••"
          />
        </div>

        <button
          type="submit"
          class="pm-btn pm-btn-primary"
          style="width: 100%; padding: 0.65rem;"
          :disabled="authStore.loading"
        >
          <span v-if="authStore.loading">Authenticating...</span>
          <template v-else>
            <span>Sign In to Clinical Console</span>
            <ArrowRight :size="16" />
          </template>
        </button>
      </form>

      <!-- Quick Role Selection for Demonstration -->
      <div class="pm-role-selector">
        <div class="pm-role-title">Fast Role Switcher (Preconfigured Access):</div>
        <div class="pm-role-grid">
          <div
            v-for="item in presetRoles"
            :key="item.role"
            class="pm-role-item"
            :class="{ active: email === item.email }"
            @click="selectRole(item)"
          >
            <div class="pm-role-top">
              <span class="pm-badge" :class="item.badge">{{ item.role }}</span>
              <CheckCircle2 v-if="email === item.email" :size="14" style="color: var(--pm-primary);" />
            </div>
            <div class="pm-role-name">{{ item.name }}</div>
            <div class="pm-role-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pm-login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background-color: var(--pm-bg-canvas);
}

.pm-login-card {
  width: 100%;
  max-width: 520px;
  background-color: var(--pm-bg-card);
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
  padding: 2rem;
}

.pm-login-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.pm-login-icon {
  width: 48px;
  height: 48px;
  background-color: var(--pm-primary-light);
  color: var(--pm-primary);
  border: 1px solid #bae6fd;
  border-radius: var(--pm-radius);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pm-login-title {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1.2;
}

.pm-login-sub {
  font-size: 0.85rem;
  color: var(--pm-text-secondary);
}

.pm-login-inst {
  font-size: 0.75rem;
  color: var(--pm-text-muted);
}

.pm-login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.pm-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pm-form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--pm-text-secondary);
}

.pm-role-selector {
  border-top: 1px solid var(--pm-border);
  padding-top: 1.25rem;
}

.pm-role-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--pm-text-muted);
  margin-bottom: 0.75rem;
}

.pm-role-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.pm-role-item {
  padding: 0.6rem;
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
  background: var(--pm-bg-card);
  cursor: pointer;
  transition: all 0.15s ease;
}

.pm-role-item:hover {
  background-color: var(--pm-bg-subtle);
  border-color: #cbd5e1;
}

.pm-role-item.active {
  border-color: var(--pm-primary);
  background-color: var(--pm-primary-light);
}

.pm-role-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.3rem;
}

.pm-role-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--pm-text-primary);
  line-height: 1.2;
}

.pm-role-desc {
  font-size: 0.68rem;
  color: var(--pm-text-muted);
  line-height: 1.3;
  margin-top: 0.2rem;
}
</style>
