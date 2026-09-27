<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useClinicalStore } from '../stores/clinical'
import { useAuthStore } from '../stores/auth'
import {
  Users,
  AlertTriangle,
  BookOpen,
  Dna,
  Search,
  Plus,
  ArrowRight,
  ShieldCheck,
  X,
} from 'lucide-vue-next'

const router = useRouter()
const clinicalStore = useClinicalStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const showNewPatientModal = ref(false)

// Form state
const newPatient = ref({
  medical_record_number: '',
  first_name: '',
  last_name: '',
  dob: '',
  sex: 'M',
  contact_phone: '',
  contact_address: '',
})
const formError = ref<string | null>(null)
const submitting = ref(false)

onMounted(async () => {
  await clinicalStore.fetchPatients()
  await clinicalStore.fetchRules()
})

const handleSearch = async () => {
  await clinicalStore.fetchPatients(searchQuery.value)
}

const calculateAge = (dobString: string): number => {
  if (!dobString) return 0
  const dob = new Date(dobString)
  const diff = Date.now() - dob.getTime()
  const ageDate = new Date(diff)
  return Math.abs(ageDate.getUTCFullYear() - 1970)
}

const openPatient = (id: string) => {
  router.push(`/patients/${id}`)
}

const handleCreatePatient = async () => {
  formError.value = null
  if (!newPatient.value.medical_record_number || !newPatient.value.first_name || !newPatient.value.last_name || !newPatient.value.dob) {
    formError.value = 'Please complete all required fields.'
    return
  }

  submitting.value = true
  try {
    const created = await clinicalStore.createPatient({
      medical_record_number: newPatient.value.medical_record_number.trim(),
      first_name: newPatient.value.first_name.trim(),
      last_name: newPatient.value.last_name.trim(),
      dob: newPatient.value.dob,
      sex: newPatient.value.sex,
      contact_info: {
        phone: newPatient.value.contact_phone.trim(),
        address: newPatient.value.contact_address.trim(),
      },
    })
    showNewPatientModal.value = false
    newPatient.value = {
      medical_record_number: '',
      first_name: '',
      last_name: '',
      dob: '',
      sex: 'M',
      contact_phone: '',
      contact_address: '',
    }
    router.push(`/patients/${created.id}`)
  } catch (err: any) {
    formError.value = err.response?.data?.detail || 'Failed to create patient.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="pm-page-container">
    <!-- Institutional Clinical Directive Banner -->
    <div class="pm-directive-strip">
      <div class="pm-directive-content">
        <ShieldCheck :size="16" style="color: var(--pm-teal); flex-shrink: 0;" />
        <span>
          <strong>Clinical Decision Support Notice:</strong> PM-CDSS assists qualified clinicians at Levy Mwanawasa Teaching Hospital with pharmacogenomic guidance. The system never autonomously prescribes or diagnoses.
        </span>
      </div>
    </div>

    <!-- Summary Metric Grid -->
    <div class="pm-metric-grid">
      <div class="pm-card pm-metric-card">
        <div class="pm-metric-top">
          <span class="pm-metric-label">Monitored Patients</span>
          <div class="pm-metric-icon">
            <Users :size="16" />
          </div>
        </div>
        <div class="pm-metric-value">{{ clinicalStore.totalPatients }}</div>
        <div class="pm-metric-sub">Active registry cohort</div>
      </div>

      <div class="pm-card pm-metric-card alert">
        <div class="pm-metric-top">
          <span class="pm-metric-label">Triggered PGx Alerts</span>
          <div class="pm-metric-icon warning">
            <AlertTriangle :size="16" />
          </div>
        </div>
        <div class="pm-metric-value">
          {{ clinicalStore.patients.reduce((acc, p) => acc + (p.active_alerts_count || 0), 0) }}
        </div>
        <div class="pm-metric-sub">Requiring clinician acknowledgment</div>
      </div>

      <div class="pm-card pm-metric-card">
        <div class="pm-metric-top">
          <span class="pm-metric-label">Active CDSS Rules</span>
          <div class="pm-metric-icon">
            <BookOpen :size="16" />
          </div>
        </div>
        <div class="pm-metric-value">{{ clinicalStore.rules.length || 6 }}</div>
        <div class="pm-metric-sub">CPIC / DPWG guidelines</div>
      </div>

      <div class="pm-card pm-metric-card">
        <div class="pm-metric-top">
          <span class="pm-metric-label">Biomarker Registry</span>
          <div class="pm-metric-icon teal">
            <Dna :size="16" />
          </div>
        </div>
        <div class="pm-metric-value">Active</div>
        <div class="pm-metric-sub">Genomics lab integration</div>
      </div>
    </div>

    <!-- Patient Directory Card -->
    <div class="pm-card">
      <div class="pm-table-toolbar">
        <div class="pm-search-box">
          <Search :size="16" class="pm-search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search by MRN, first or last name..."
            class="pm-input pm-search-input"
            @keyup.enter="handleSearch"
          />
          <button type="button" class="pm-btn pm-btn-secondary pm-btn-sm" @click="handleSearch">
            Filter
          </button>
        </div>

        <button
          v-if="authStore.isClinician || authStore.isAdmin"
          type="button"
          class="pm-btn pm-btn-primary"
          @click="showNewPatientModal = true"
        >
          <Plus :size="16" />
          <span>New Patient</span>
        </button>
      </div>

      <!-- Clinical Table -->
      <div class="pm-table-wrapper">
        <table class="pm-table">
          <thead>
            <tr>
              <th>Medical Record No.</th>
              <th>Patient Name</th>
              <th>Age / DOB</th>
              <th>Sex</th>
              <th>CDSS Status</th>
              <th style="text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="clinicalStore.loading">
              <td colspan="6" class="pm-table-empty">Loading patient records...</td>
            </tr>
            <tr v-else-if="clinicalStore.patients.length === 0">
              <td colspan="6" class="pm-table-empty">No patient records found matching search criteria.</td>
            </tr>
            <tr
              v-for="p in clinicalStore.patients"
              v-else
              :key="p.id"
              class="pm-table-row"
              @click="openPatient(p.id)"
            >
              <td class="pm-font-mono pm-text-bold">
                {{ p.medical_record_number }}
              </td>
              <td>
                <span class="pm-patient-name">{{ p.first_name }} {{ p.last_name }}</span>
              </td>
              <td>
                {{ calculateAge(p.dob) }} yrs ({{ p.dob }})
              </td>
              <td>
                <span class="pm-badge pm-badge-neutral">{{ p.sex }}</span>
              </td>
              <td>
                <span
                  v-if="(p.active_alerts_count || 0) > 0"
                  class="pm-badge pm-badge-critical"
                >
                  <AlertTriangle :size="12" style="margin-right: 4px;" />
                  {{ p.active_alerts_count }} Active Alert(s)
                </span>
                <span v-else class="pm-badge pm-badge-success">
                  No Contradictions
                </span>
              </td>
              <td style="text-align: right;">
                <button
                  type="button"
                  class="pm-btn pm-btn-secondary pm-btn-sm"
                  @click.stop="openPatient(p.id)"
                >
                  <span>Open Chart</span>
                  <ArrowRight :size="14" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New Patient Modal -->
    <div v-if="showNewPatientModal" class="pm-modal-overlay">
      <div class="pm-modal-card">
        <div class="pm-modal-header">
          <h3>Register New Patient</h3>
          <button type="button" class="pm-modal-close" @click="showNewPatientModal = false">
            <X :size="18" />
          </button>
        </div>

        <div v-if="formError" class="pm-alert-banner critical" style="margin-bottom: 1rem;">
          {{ formError }}
        </div>

        <form @submit.prevent="handleCreatePatient" class="pm-modal-form">
          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Medical Record Number (MRN) *</label>
              <input
                v-model="newPatient.medical_record_number"
                type="text"
                required
                placeholder="e.g. LMTH-2024-999"
                class="pm-input"
              />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Biological Sex *</label>
              <select v-model="newPatient.sex" class="pm-input">
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">First Name *</label>
              <input
                v-model="newPatient.first_name"
                type="text"
                required
                placeholder="First name"
                class="pm-input"
              />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Last Name *</label>
              <input
                v-model="newPatient.last_name"
                type="text"
                required
                placeholder="Last name"
                class="pm-input"
              />
            </div>
          </div>

          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Date of Birth *</label>
              <input
                v-model="newPatient.dob"
                type="date"
                required
                class="pm-input"
              />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Contact Phone</label>
              <input
                v-model="newPatient.contact_phone"
                type="text"
                placeholder="+260-977-000000"
                class="pm-input"
              />
            </div>
          </div>

          <div class="pm-form-group">
            <label class="pm-form-label">Residential Address</label>
            <input
              v-model="newPatient.contact_address"
              type="text"
              placeholder="e.g. Plot 12, Lusaka"
              class="pm-input"
            />
          </div>

          <div class="pm-modal-footer">
            <button
              type="button"
              class="pm-btn pm-btn-secondary"
              @click="showNewPatientModal = false"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="pm-btn pm-btn-primary"
              :disabled="submitting"
            >
              {{ submitting ? 'Saving...' : 'Create Patient Record' }}
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
  gap: 1.5rem;
}

.pm-directive-strip {
  background-color: var(--pm-teal-light);
  border: 1px solid #99f6e4;
  border-radius: var(--pm-radius);
  padding: 0.75rem 1rem;
}

.pm-directive-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: #115e59;
}

.pm-metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.pm-metric-card {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pm-metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pm-metric-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--pm-text-muted);
}

.pm-metric-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--pm-radius);
  background-color: var(--pm-primary-light);
  color: var(--pm-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pm-metric-icon.warning {
  background-color: var(--pm-warning-bg);
  color: var(--pm-warning-border);
}

.pm-metric-icon.teal {
  background-color: var(--pm-teal-light);
  color: var(--pm-teal);
}

.pm-metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--pm-text-primary);
  line-height: 1.1;
}

.pm-metric-sub {
  font-size: 0.75rem;
  color: var(--pm-text-muted);
}

.pm-table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.pm-search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  flex: 1;
  max-width: 480px;
}

.pm-search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--pm-text-muted);
  pointer-events: none;
}

.pm-search-input {
  padding-left: 2.25rem;
}

.pm-table-wrapper {
  overflow-x: auto;
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
}

.pm-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
}

.pm-table th {
  background-color: var(--pm-bg-subtle);
  color: var(--pm-text-secondary);
  font-weight: 600;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--pm-border);
}

.pm-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--pm-border);
  color: var(--pm-text-primary);
}

.pm-table-row {
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.pm-table-row:hover {
  background-color: #f8fafc;
}

.pm-table-empty {
  text-align: center;
  color: var(--pm-text-muted);
  padding: 2rem !important;
}

.pm-font-mono {
  font-family: var(--font-mono);
}

.pm-text-bold {
  font-weight: 600;
}

.pm-patient-name {
  font-weight: 500;
  color: var(--pm-text-primary);
}

/* Modal */
.pm-modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 1.5rem;
}

.pm-modal-card {
  width: 100%;
  max-width: 600px;
  background-color: var(--pm-bg-card);
  border-radius: var(--pm-radius);
  border: 1px solid var(--pm-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 1.5rem;
}

.pm-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--pm-border);
}

.pm-modal-close {
  background: none;
  border: none;
  color: var(--pm-text-muted);
  cursor: pointer;
}

.pm-modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pm-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.pm-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.pm-form-label {
  font-size: 0.775rem;
  font-weight: 600;
  color: var(--pm-text-secondary);
}

.pm-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--pm-border);
}
</style>
