<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { UserCheck, Plus, X, ShieldAlert, CheckCircle2 } from 'lucide-vue-next'

const users = ref<any[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const submitting = ref(false)
const errorMsg = ref<string | null>(null)
const successMsg = ref<string | null>(null)

const form = ref({
  email: '',
  full_name: '',
  role: 'Clinician',
  password: '',
  is_active: true,
})

onMounted(async () => {
  await loadUsers()
})

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await api.get('/users')
    users.value = res.data
  } catch (err: any) {
    console.error('Failed to load users', err)
  } finally {
    loading.value = false
  }
}

const handleCreateUser = async () => {
  if (!form.value.email || !form.value.full_name || !form.value.password) {
    errorMsg.value = 'Please provide all required fields.'
    return
  }
  submitting.value = true
  errorMsg.value = null
  successMsg.value = null
  try {
    await api.post('/users', form.value)
    successMsg.value = `User ${form.value.email} provisioned successfully.`
    showCreateModal.value = false
    form.value = {
      email: '',
      full_name: '',
      role: 'Clinician',
      password: '',
      is_active: true,
    }
    await loadUsers()
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'Failed to create user.'
  } finally {
    submitting.value = false
  }
}

const toggleActive = async (user: any) => {
  try {
    await api.put(`/users/${user.id}`, { is_active: !user.is_active })
    user.is_active = !user.is_active
  } catch (err) {
    console.error('Failed to toggle status', err)
  }
}

const formatRoleBadge = (role: string) => {
  switch (role) {
    case 'Administrator': return 'pm-badge-neutral'
    case 'Clinician': return 'pm-badge-info'
    case 'Lab_Officer': return 'pm-badge-warning'
    case 'Auditor': return 'pm-badge-success'
    default: return 'pm-badge-neutral'
  }
}
</script>

<template>
  <div class="pm-page-container">
    <div class="pm-card-header" style="margin-bottom: 0;">
      <div>
        <h2 style="font-size: 1.25rem;">Institutional Access Governance & RBAC</h2>
        <p style="font-size: 0.8rem; color: var(--pm-text-muted);">
          System Administrator Console • Role Provisioning & Clinical Account Controls
        </p>
      </div>
      <button type="button" class="pm-btn pm-btn-primary" @click="showCreateModal = true">
        <Plus :size="16" />
        <span>Provision Staff Account</span>
      </button>
    </div>

    <div v-if="successMsg" class="pm-alert-banner success">
      <CheckCircle2 :size="16" />
      <span>{{ successMsg }}</span>
    </div>

    <!-- Users Table -->
    <div class="pm-card">
      <div class="pm-table-wrapper">
        <table class="pm-table">
          <thead>
            <tr>
              <th>Full Name</th>
              <th>Hospital Email</th>
              <th>Assigned RBAC Role</th>
              <th>Status</th>
              <th>Created Date</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="pm-table-empty">Loading users...</td>
            </tr>
            <tr v-for="u in users" v-else :key="u.id">
              <td class="pm-text-bold">{{ u.full_name }}</td>
              <td class="pm-font-mono">{{ u.email }}</td>
              <td>
                <span class="pm-badge" :class="formatRoleBadge(u.role)">
                  {{ u.role }}
                </span>
              </td>
              <td>
                <span class="pm-badge" :class="u.is_active ? 'pm-badge-success' : 'pm-badge-critical'">
                  {{ u.is_active ? 'Active' : 'Deactivated' }}
                </span>
              </td>
              <td style="font-size: 0.8rem;">{{ new Date(u.created_at).toLocaleDateString() }}</td>
              <td style="text-align: right;">
                <button
                  type="button"
                  class="pm-btn pm-btn-secondary pm-btn-sm"
                  @click="toggleActive(u)"
                >
                  {{ u.is_active ? 'Deactivate' : 'Activate' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateModal" class="pm-modal-overlay">
      <div class="pm-modal-card">
        <div class="pm-modal-header">
          <h3>Provision Staff Account</h3>
          <button type="button" class="pm-modal-close" @click="showCreateModal = false"><X :size="18" /></button>
        </div>

        <div v-if="errorMsg" class="pm-alert-banner critical" style="margin-bottom: 1rem;">
          {{ errorMsg }}
        </div>

        <form @submit.prevent="handleCreateUser" class="pm-modal-form">
          <div class="pm-form-group">
            <label class="pm-form-label">Full Name & Clinical Designation *</label>
            <input
              v-model="form.full_name"
              type="text"
              required
              placeholder="e.g. Dr. Jane Zulu (Registrar)"
              class="pm-input"
            />
          </div>

          <div class="pm-form-group">
            <label class="pm-form-label">Institutional Email *</label>
            <input
              v-model="form.email"
              type="email"
              required
              placeholder="e.g. jzulu@lmth.gov.zm"
              class="pm-input"
            />
          </div>

          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">RBAC System Role *</label>
              <select v-model="form.role" class="pm-input">
                <option value="Clinician">Clinician (Charts, Meds, CDSS)</option>
                <option value="Administrator">Administrator (Full Access)</option>
                <option value="Lab_Officer">Lab_Officer (Genomics Ingestion)</option>
                <option value="Auditor">Auditor (Read-Only Event Log)</option>
              </select>
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Temporary Password (min 8 chars) *</label>
              <input
                v-model="form.password"
                type="password"
                required
                minlength="8"
                placeholder="••••••••••••"
                class="pm-input"
              />
            </div>
          </div>

          <div class="pm-modal-footer">
            <button type="button" class="pm-btn pm-btn-secondary" @click="showCreateModal = false">Cancel</button>
            <button type="submit" class="pm-btn pm-btn-primary" :disabled="submitting">
              {{ submitting ? 'Provisioning...' : 'Provision Account' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pm-page-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.pm-font-mono {
  font-family: var(--font-mono);
}

.pm-text-bold {
  font-weight: 600;
}
</style>
