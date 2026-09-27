<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClinicalStore, type AlertInstance } from '../stores/clinical'
import { useAuthStore } from '../stores/auth'
import {
  ArrowLeft,
  Activity,
  AlertTriangle,
  ShieldAlert,
  Dna,
  Pill,
  FileText,
  CheckCircle,
  Plus,
  RefreshCw,
  BookOpen,
  X,
  ExternalLink,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const clinicalStore = useClinicalStore()
const authStore = useAuthStore()

const patientId = route.params.id as string
const activeTab = ref<'meds' | 'genomics' | 'diagnoses' | 'alerts'>('meds')

// Modals
const showMedModal = ref(false)
const showGenomicModal = ref(false)
const showDiagnosisModal = ref(false)
const showAckModal = ref(false)
const selectedAlert = ref<AlertInstance | null>(null)
const clinicianNote = ref('')
const overrideAlert = ref(false)
const ackSubmitting = ref(false)
const ackError = ref<string | null>(null)

// Forms
const todayDate = () => new Date().toISOString().slice(0, 10)

const medForm = ref({
  drug_name: '',
  dosage: '',
  frequency: '',
  start_date: todayDate(),
})

const genomicForm = ref({
  gene_symbol: 'CYP2C19',
  variant_allele: '*2/*2',
  phenotype: 'Poor Metabolizer',
  test_date: todayDate(),
})

const diagForm = ref({
  icd10_code: '',
  description: '',
  date_diagnosed: todayDate(),
})

onMounted(async () => {
  await clinicalStore.fetchPatientDetail(patientId)
})

const patient = computed(() => clinicalStore.currentPatient)

const activeAlerts = computed(() => {
  if (!patient.value?.alerts) return []
  return patient.value.alerts.filter(a => a.status === 'TRIGGERED')
})

const calculateAge = (dobString?: string): number => {
  if (!dobString) return 0
  const dob = new Date(dobString)
  const diff = Date.now() - dob.getTime()
  return Math.abs(new Date(diff).getUTCFullYear() - 1970)
}

const runEvaluation = async () => {
  await clinicalStore.evaluatePatientCDSS(patientId)
}

const openAckModal = (alert: AlertInstance) => {
  selectedAlert.value = alert
  clinicianNote.value = ''
  overrideAlert.value = false
  ackError.value = null
  showAckModal.value = true
}

const handleAcknowledge = async () => {
  if (!selectedAlert.value) return
  if (!clinicianNote.value.trim()) {
    ackError.value = 'Please provide a clinical note or justification before signing acknowledgment.'
    return
  }
  ackSubmitting.value = true
  ackError.value = null
  try {
    await clinicalStore.acknowledgeAlert(selectedAlert.value.id, clinicianNote.value.trim(), overrideAlert.value)
    showAckModal.value = false
    selectedAlert.value = null
  } catch (err: any) {
    ackError.value = err.response?.data?.detail || 'Failed to acknowledge alert.'
  } finally {
    ackSubmitting.value = false
  }
}

const handleAddMed = async () => {
  if (!medForm.value.drug_name || !medForm.value.dosage) return
  await clinicalStore.addMedication(patientId, {
    drug_name: medForm.value.drug_name,
    dosage: medForm.value.dosage,
    frequency: medForm.value.frequency,
    start_date: medForm.value.start_date,
  })
  showMedModal.value = false
  medForm.value = {
    drug_name: '',
    dosage: '',
    frequency: '',
    start_date: todayDate(),
  }
}

const handleAddGenomic = async () => {
  if (!genomicForm.value.gene_symbol || !genomicForm.value.variant_allele) return
  await clinicalStore.addGenomicRecord(patientId, {
    gene_symbol: genomicForm.value.gene_symbol,
    variant_allele: genomicForm.value.variant_allele,
    phenotype: genomicForm.value.phenotype,
    test_date: genomicForm.value.test_date,
  })
  showGenomicModal.value = false
}

const handleAddDiag = async () => {
  if (!diagForm.value.icd10_code || !diagForm.value.description) return
  await clinicalStore.addDiagnosis(patientId, {
    icd10_code: diagForm.value.icd10_code,
    description: diagForm.value.description,
    date_diagnosed: diagForm.value.date_diagnosed,
  })
  showDiagnosisModal.value = false
  diagForm.value = {
    icd10_code: '',
    description: '',
    date_diagnosed: todayDate(),
  }
}
</script>

<template>
  <div class="pm-page-container">
    <!-- Top Navigation Bar -->
    <div class="pm-top-nav">
      <button type="button" class="pm-btn pm-btn-secondary pm-btn-sm" @click="router.push('/')">
        <ArrowLeft :size="14" />
        <span>Return to Patient Registry</span>
      </button>

      <button
        v-if="authStore.canAcknowledgeAlerts"
        type="button"
        class="pm-btn pm-btn-primary pm-btn-sm"
        :disabled="clinicalStore.evaluating"
        @click="runEvaluation"
      >
        <RefreshCw :size="14" :class="{ 'pm-spin': clinicalStore.evaluating }" />
        <span>{{ clinicalStore.evaluating ? 'Evaluating...' : 'Re-Evaluate CDSS' }}</span>
      </button>
    </div>

    <!-- Patient Header Card -->
    <div v-if="patient" class="pm-card pm-patient-banner">
      <div class="pm-banner-main">
        <div class="pm-banner-identity">
          <div class="pm-avatar-box">
            {{ patient.first_name[0] }}{{ patient.last_name[0] }}
          </div>
          <div>
            <div class="pm-banner-name-row">
              <h1 class="pm-patient-heading">{{ patient.first_name }} {{ patient.last_name }}</h1>
              <span class="pm-badge pm-badge-neutral pm-font-mono">{{ patient.medical_record_number }}</span>
              <span class="pm-badge" :class="patient.sex === 'M' ? 'pm-badge-info' : 'pm-badge-warning'">
                {{ patient.sex === 'M' ? 'Male' : patient.sex === 'F' ? 'Female' : patient.sex }}
              </span>
            </div>
            <div class="pm-banner-sub">
              <span><strong>DOB:</strong> {{ patient.dob }} ({{ calculateAge(patient.dob) }} yrs)</span>
              <span v-if="patient.contact_info?.phone"><strong>Tel:</strong> {{ patient.contact_info.phone }}</span>
              <span v-if="patient.contact_info?.address"><strong>Address:</strong> {{ patient.contact_info.address }}</span>
            </div>
          </div>
        </div>

        <div class="pm-banner-alert-summary">
          <div v-if="activeAlerts.length > 0" class="pm-alert-pill critical">
            <AlertTriangle :size="16" />
            <span>{{ activeAlerts.length }} Unacknowledged PGx Alert(s)</span>
          </div>
          <div v-else class="pm-alert-pill safe">
            <CheckCircle :size="16" />
            <span>No Unacknowledged PGx Conflicts</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Active CDSS Alerts Container -->
    <div v-if="activeAlerts.length > 0" class="pm-alerts-container">
      <div
        v-for="alert in activeAlerts"
        :key="alert.id"
        class="pm-cdss-alert-card"
        :class="alert.severity.toLowerCase()"
      >
        <div class="pm-cdss-alert-header">
          <div class="pm-cdss-alert-title-row">
            <span class="pm-badge" :class="alert.severity === 'CRITICAL' ? 'pm-badge-critical' : 'pm-badge-warning'">
              {{ alert.severity }} PHARMACOGENOMIC CONTRAINDICATION
            </span>
            <span class="pm-cdss-alert-rulecode pm-font-mono">
              {{ alert.rule?.rule_code || 'PGX-RULE' }}
            </span>
          </div>
          <button
            v-if="authStore.canAcknowledgeAlerts"
            type="button"
            class="pm-btn pm-btn-danger pm-btn-sm"
            @click="openAckModal(alert)"
          >
            Review & Acknowledge
          </button>
        </div>

        <div class="pm-cdss-alert-body">
          <p class="pm-cdss-alert-message">{{ alert.message }}</p>

          <!-- Evidence Badges -->
          <div v-if="alert.evidence_data" class="pm-evidence-box">
            <div class="pm-evidence-chip">
              <Pill :size="12" />
              <span>Drug: <strong>{{ alert.evidence_data.drug_name }}</strong> ({{ alert.evidence_data.dosage }})</span>
            </div>
            <div class="pm-evidence-chip">
              <Dna :size="12" />
              <span>Gene: <strong>{{ alert.evidence_data.gene_symbol }}</strong></span>
            </div>
            <div class="pm-evidence-chip">
              <span>Allele: <strong>{{ alert.evidence_data.variant_allele }}</strong></span>
            </div>
            <div class="pm-evidence-chip">
              <span>Phenotype: <strong>{{ alert.evidence_data.phenotype }}</strong></span>
            </div>
          </div>

          <!-- Recommendation Preview -->
          <div v-if="alert.rule" class="pm-recommendation-box">
            <strong>Clinical Recommendation:</strong> {{ alert.rule.recommendation }}
          </div>
        </div>
      </div>
    </div>

    <!-- Clinical Details Tabs -->
    <div class="pm-card pm-tabs-card">
      <div class="pm-tabs-header">
        <button
          type="button"
          class="pm-tab-btn"
          :class="{ active: activeTab === 'meds' }"
          @click="activeTab = 'meds'"
        >
          <Pill :size="16" />
          <span>Active Medications ({{ patient?.medications?.length || 0 }})</span>
        </button>

        <button
          type="button"
          class="pm-tab-btn"
          :class="{ active: activeTab === 'genomics' }"
          @click="activeTab = 'genomics'"
        >
          <Dna :size="16" />
          <span>Genomic Biomarkers ({{ patient?.genomic_records?.length || 0 }})</span>
        </button>

        <button
          type="button"
          class="pm-tab-btn"
          :class="{ active: activeTab === 'diagnoses' }"
          @click="activeTab = 'diagnoses'"
        >
          <FileText :size="16" />
          <span>Diagnoses ({{ patient?.diagnoses?.length || 0 }})</span>
        </button>

        <button
          type="button"
          class="pm-tab-btn"
          :class="{ active: activeTab === 'alerts' }"
          @click="activeTab = 'alerts'"
        >
          <AlertTriangle :size="16" />
          <span>Alert History ({{ patient?.alerts?.length || 0 }})</span>
        </button>
      </div>

      <!-- Tab Content: Medications -->
      <div v-if="activeTab === 'meds'" class="pm-tab-body">
        <div class="pm-section-toolbar">
          <span class="pm-section-title">Current Pharmacological Regimen</span>
          <button
            v-if="authStore.isClinician || authStore.isAdmin"
            type="button"
            class="pm-btn pm-btn-secondary pm-btn-sm"
            @click="showMedModal = true"
          >
            <Plus :size="14" />
            <span>Prescribe Medication</span>
          </button>
        </div>

        <div class="pm-table-wrapper">
          <table class="pm-table">
            <thead>
              <tr>
                <th>Drug Name</th>
                <th>Dosage</th>
                <th>Frequency</th>
                <th>Start Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!patient?.medications?.length">
                <td colspan="5" class="pm-table-empty">No active medications registered.</td>
              </tr>
              <tr v-for="m in patient?.medications" v-else :key="m.id">
                <td class="pm-text-bold">{{ m.drug_name }}</td>
                <td>{{ m.dosage }}</td>
                <td>{{ m.frequency }}</td>
                <td>{{ m.start_date }}</td>
                <td>
                  <span class="pm-badge" :class="m.active ? 'pm-badge-success' : 'pm-badge-neutral'">
                    {{ m.active ? 'Active' : 'Discontinued' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab Content: Genomics -->
      <div v-if="activeTab === 'genomics'" class="pm-tab-body">
        <div class="pm-section-toolbar">
          <span class="pm-section-title">Verified Pharmacogenomic Biomarkers</span>
          <button
            v-if="authStore.canModifyGenomics"
            type="button"
            class="pm-btn pm-btn-secondary pm-btn-sm"
            @click="showGenomicModal = true"
          >
            <Plus :size="14" />
            <span>Add Genomic Entry</span>
          </button>
        </div>

        <div class="pm-table-wrapper">
          <table class="pm-table">
            <thead>
              <tr>
                <th>Gene Symbol</th>
                <th>Variant / Allele</th>
                <th>Metabolizer Phenotype</th>
                <th>Test Date</th>
                <th>Verification</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!patient?.genomic_records?.length">
                <td colspan="5" class="pm-table-empty">No genomic test results recorded yet.</td>
              </tr>
              <tr v-for="g in patient?.genomic_records" v-else :key="g.id">
                <td class="pm-font-mono pm-text-bold">{{ g.gene_symbol }}</td>
                <td class="pm-font-mono">{{ g.variant_allele }}</td>
                <td>
                  <span
                    class="pm-badge"
                    :class="g.phenotype.includes('Poor') || g.phenotype.includes('Risk') ? 'pm-badge-critical' : 'pm-badge-info'"
                  >
                    {{ g.phenotype }}
                  </span>
                </td>
                <td>{{ g.test_date }}</td>
                <td>
                  <span class="pm-badge pm-badge-success">Verified Lab Officer</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab Content: Diagnoses -->
      <div v-if="activeTab === 'diagnoses'" class="pm-tab-body">
        <div class="pm-section-toolbar">
          <span class="pm-section-title">Clinical Diagnoses & ICD-10 Coding</span>
          <button
            v-if="authStore.isClinician || authStore.isAdmin"
            type="button"
            class="pm-btn pm-btn-secondary pm-btn-sm"
            @click="showDiagnosisModal = true"
          >
            <Plus :size="14" />
            <span>Add Diagnosis</span>
          </button>
        </div>

        <div class="pm-table-wrapper">
          <table class="pm-table">
            <thead>
              <tr>
                <th>ICD-10 Code</th>
                <th>Clinical Description</th>
                <th>Date Diagnosed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!patient?.diagnoses?.length">
                <td colspan="3" class="pm-table-empty">No clinical diagnoses registered.</td>
              </tr>
              <tr v-for="d in patient?.diagnoses" v-else :key="d.id">
                <td class="pm-font-mono pm-text-bold">{{ d.icd10_code }}</td>
                <td>{{ d.description }}</td>
                <td>{{ d.date_diagnosed }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Tab Content: Alert History -->
      <div v-if="activeTab === 'alerts'" class="pm-tab-body">
        <div class="pm-section-toolbar">
          <span class="pm-section-title">CDSS Alert Audit & Clinical Acknowledgment Trail</span>
        </div>

        <div class="pm-table-wrapper">
          <table class="pm-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Triggered At</th>
                <th>Message</th>
                <th>Status</th>
                <th>Clinician Justification / Note</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!patient?.alerts?.length">
                <td colspan="5" class="pm-table-empty">No alerts triggered for this patient.</td>
              </tr>
              <tr v-for="a in patient?.alerts" v-else :key="a.id">
                <td>
                  <span
                    class="pm-badge"
                    :class="a.severity === 'CRITICAL' ? 'pm-badge-critical' : 'pm-badge-warning'"
                  >
                    {{ a.severity }}
                  </span>
                </td>
                <td>{{ new Date(a.triggered_at).toLocaleString() }}</td>
                <td style="max-width: 320px;">{{ a.message }}</td>
                <td>
                  <span
                    class="pm-badge"
                    :class="a.status === 'TRIGGERED' ? 'pm-badge-critical' : a.status === 'ACKNOWLEDGED' ? 'pm-badge-success' : 'pm-badge-warning'"
                  >
                    {{ a.status }}
                  </span>
                </td>
                <td>
                  <div v-if="a.clinician_note" style="font-size: 0.8rem;">
                    <em>"{{ a.clinician_note }}"</em>
                    <div v-if="a.acknowledged_at" style="color: var(--pm-text-muted); font-size: 0.7rem;">
                      Ack at: {{ new Date(a.acknowledged_at).toLocaleString() }}
                    </div>
                  </div>
                  <span v-else style="color: var(--pm-text-muted); font-style: italic;">
                    Pending Clinician Review
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- RULE EXPLANATION & ALERT ACKNOWLEDGEMENT MODAL -->
    <div v-if="showAckModal && selectedAlert" class="pm-modal-overlay">
      <div class="pm-modal-card pm-ack-modal">
        <div class="pm-modal-header">
          <div class="pm-modal-header-left">
            <span
              class="pm-badge"
              :class="selectedAlert.severity === 'CRITICAL' ? 'pm-badge-critical' : 'pm-badge-warning'"
            >
              {{ selectedAlert.severity }} ALERT REVIEW
            </span>
            <span class="pm-font-mono pm-text-muted" style="font-size: 0.8rem;">
              {{ selectedAlert.rule?.rule_code }}
            </span>
          </div>
          <button type="button" class="pm-modal-close" @click="showAckModal = false">
            <X :size="18" />
          </button>
        </div>

        <div v-if="ackError" class="pm-alert-banner critical" style="margin-bottom: 1rem;">
          {{ ackError }}
        </div>

        <div class="pm-ack-content">
          <!-- Mechanistic Summary -->
          <div class="pm-ack-section">
            <h4 class="pm-ack-title">Pharmacogenomic Conflict Description</h4>
            <p class="pm-ack-text">{{ selectedAlert.message }}</p>
          </div>

          <!-- Exact Trigger Evidence -->
          <div v-if="selectedAlert.evidence_data" class="pm-ack-section">
            <h4 class="pm-ack-title">Trigger Evidence (Exact Biomarker Values)</h4>
            <div class="pm-ack-evidence-grid">
              <div class="pm-ack-evidence-card">
                <span class="pm-ack-evidence-label">Active Prescription</span>
                <span class="pm-ack-evidence-val">{{ selectedAlert.evidence_data.drug_name }} ({{ selectedAlert.evidence_data.dosage }})</span>
              </div>
              <div class="pm-ack-evidence-card">
                <span class="pm-ack-evidence-label">Patient Gene Symbol</span>
                <span class="pm-ack-evidence-val pm-font-mono">{{ selectedAlert.evidence_data.gene_symbol }}</span>
              </div>
              <div class="pm-ack-evidence-card">
                <span class="pm-ack-evidence-label">Observed Allele</span>
                <span class="pm-ack-evidence-val pm-font-mono">{{ selectedAlert.evidence_data.variant_allele }}</span>
              </div>
              <div class="pm-ack-evidence-card">
                <span class="pm-ack-evidence-label">Clinical Phenotype</span>
                <span class="pm-ack-evidence-val">{{ selectedAlert.evidence_data.phenotype }}</span>
              </div>
            </div>
          </div>

          <!-- Institutional Reference & Recommendation -->
          <div v-if="selectedAlert.rule" class="pm-ack-section pm-ack-rec-box">
            <h4 class="pm-ack-title" style="color: #0369a1;">Clinical Action Recommendation</h4>
            <p style="margin-bottom: 0.5rem; font-size: 0.85rem;">{{ selectedAlert.rule.recommendation }}</p>
            <div style="font-size: 0.75rem; color: var(--pm-text-muted);">
              <strong>Guideline Citation:</strong> {{ selectedAlert.rule.clinical_reference }}
            </div>
          </div>

          <!-- Clinician Input -->
          <div class="pm-ack-section">
            <label class="pm-form-label" for="ack-note">
              Clinician Acknowledgment Note & Rationale *
            </label>
            <textarea
              id="ack-note"
              v-model="clinicianNote"
              rows="3"
              class="pm-input"
              placeholder="Record therapeutic adjustments, alternative drugs selected, or rationale for clinical continuation..."
            ></textarea>
          </div>

          <!-- Override Checkbox -->
          <div class="pm-ack-override">
            <input
              id="override-checkbox"
              v-model="overrideAlert"
              type="checkbox"
            />
            <label for="override-checkbox">
              <strong>Clinical Override:</strong> Proceed with prescription despite guideline warning (Requires clinical justification in note above).
            </label>
          </div>
        </div>

        <div class="pm-modal-footer">
          <button
            type="button"
            class="pm-btn pm-btn-secondary"
            @click="showAckModal = false"
          >
            Cancel
          </button>
          <button
            type="button"
            class="pm-btn pm-btn-primary"
            :disabled="ackSubmitting"
            @click="handleAcknowledge"
          >
            {{ ackSubmitting ? 'Signing...' : 'Acknowledge & Sign Alert' }}
          </button>
        </div>
      </div>
    </div>

    <!-- PRESCRIBE MEDICATION MODAL -->
    <div v-if="showMedModal" class="pm-modal-overlay">
      <div class="pm-modal-card">
        <div class="pm-modal-header">
          <h3>Prescribe Patient Medication</h3>
          <button type="button" class="pm-modal-close" @click="showMedModal = false"><X :size="18" /></button>
        </div>
        <form @submit.prevent="handleAddMed" class="pm-modal-form">
          <div class="pm-form-group">
            <label class="pm-form-label">Drug Name *</label>
            <input
              v-model="medForm.drug_name"
              type="text"
              required
              placeholder="e.g. Clopidogrel, Abacavir, Warfarin, Allopurinol"
              class="pm-input"
            />
          </div>
          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Dosage *</label>
              <input v-model="medForm.dosage" type="text" required placeholder="e.g. 75 mg" class="pm-input" />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Frequency *</label>
              <input v-model="medForm.frequency" type="text" required placeholder="e.g. Once daily" class="pm-input" />
            </div>
          </div>
          <div class="pm-form-group">
            <label class="pm-form-label">Start Date *</label>
            <input v-model="medForm.start_date" type="date" required class="pm-input" />
          </div>
          <div class="pm-modal-footer">
            <button type="button" class="pm-btn pm-btn-secondary" @click="showMedModal = false">Cancel</button>
            <button type="submit" class="pm-btn pm-btn-primary">Prescribe & Check CDSS</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ADD GENOMIC RECORD MODAL -->
    <div v-if="showGenomicModal" class="pm-modal-overlay">
      <div class="pm-modal-card">
        <div class="pm-modal-header">
          <h3>Add Genomic Biomarker Entry</h3>
          <button type="button" class="pm-modal-close" @click="showGenomicModal = false"><X :size="18" /></button>
        </div>
        <form @submit.prevent="handleAddGenomic" class="pm-modal-form">
          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Gene Symbol *</label>
              <select v-model="genomicForm.gene_symbol" class="pm-input">
                <option value="CYP2C19">CYP2C19</option>
                <option value="HLA-B">HLA-B</option>
                <option value="CYP2D6">CYP2D6</option>
                <option value="TPMT">TPMT</option>
                <option value="VKORC1">VKORC1</option>
                <option value="DPYD">DPYD</option>
              </select>
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Variant / Allele *</label>
              <input
                v-model="genomicForm.variant_allele"
                type="text"
                required
                placeholder="e.g. *2/*2, *57:01 (Positive)"
                class="pm-input"
              />
            </div>
          </div>
          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Phenotype *</label>
              <input
                v-model="genomicForm.phenotype"
                type="text"
                required
                placeholder="e.g. Poor Metabolizer, Hypersensitivity Risk"
                class="pm-input"
              />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Test Date *</label>
              <input v-model="genomicForm.test_date" type="date" required class="pm-input" />
            </div>
          </div>
          <div class="pm-modal-footer">
            <button type="button" class="pm-btn pm-btn-secondary" @click="showGenomicModal = false">Cancel</button>
            <button type="submit" class="pm-btn pm-btn-primary">Save & Validate CDSS</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ADD DIAGNOSIS MODAL -->
    <div v-if="showDiagnosisModal" class="pm-modal-overlay">
      <div class="pm-modal-card">
        <div class="pm-modal-header">
          <h3>Record Clinical Diagnosis</h3>
          <button type="button" class="pm-modal-close" @click="showDiagnosisModal = false"><X :size="18" /></button>
        </div>
        <form @submit.prevent="handleAddDiag" class="pm-modal-form">
          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">ICD-10 Code *</label>
              <input v-model="diagForm.icd10_code" type="text" required placeholder="e.g. I25.10, B20" class="pm-input" />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Date Diagnosed *</label>
              <input v-model="diagForm.date_diagnosed" type="date" required class="pm-input" />
            </div>
          </div>
          <div class="pm-form-group">
            <label class="pm-form-label">Description *</label>
            <input v-model="diagForm.description" type="text" required placeholder="Clinical description" class="pm-input" />
          </div>
          <div class="pm-modal-footer">
            <button type="button" class="pm-btn pm-btn-secondary" @click="showDiagnosisModal = false">Cancel</button>
            <button type="submit" class="pm-btn pm-btn-primary">Save Diagnosis</button>
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

.pm-top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pm-patient-banner {
  padding: 1.5rem;
}

.pm-banner-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.pm-banner-identity {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.pm-avatar-box {
  width: 52px;
  height: 52px;
  border-radius: var(--pm-radius);
  background-color: var(--pm-primary-light);
  color: var(--pm-primary);
  font-size: 1.25rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #bae6fd;
}

.pm-banner-name-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.25rem;
}

.pm-patient-heading {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--pm-text-primary);
}

.pm-banner-sub {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  font-size: 0.8rem;
  color: var(--pm-text-secondary);
  flex-wrap: wrap;
}

.pm-alert-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--pm-radius);
  font-size: 0.825rem;
  font-weight: 600;
}

.pm-alert-pill.critical {
  background-color: var(--pm-critical-bg);
  color: var(--pm-critical-text);
  border: 1px solid var(--pm-critical-border);
}

.pm-alert-pill.safe {
  background-color: var(--pm-success-bg);
  color: var(--pm-success-text);
  border: 1px solid var(--pm-success-border);
}

/* CDSS Alert Banner Card */
.pm-alerts-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pm-cdss-alert-card {
  background-color: var(--pm-bg-card);
  border-radius: var(--pm-radius);
  padding: 1.25rem;
}

.pm-cdss-alert-card.critical {
  border: 1px solid var(--pm-critical-border);
  border-left: 6px solid var(--pm-critical-border);
  background-color: #fff8f8;
}

.pm-cdss-alert-card.warning {
  border: 1px solid var(--pm-warning-border);
  border-left: 6px solid var(--pm-warning-border);
  background-color: #fffdf5;
}

.pm-cdss-alert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pm-cdss-alert-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pm-cdss-alert-rulecode {
  font-size: 0.75rem;
  color: var(--pm-text-muted);
}

.pm-cdss-alert-message {
  font-size: 0.9rem;
  color: var(--pm-text-primary);
  line-height: 1.4;
  margin-bottom: 0.75rem;
}

.pm-evidence-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}

.pm-evidence-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background-color: #ffffff;
  border: 1px solid var(--pm-border);
  padding: 0.25rem 0.5rem;
  border-radius: var(--pm-radius);
  font-size: 0.75rem;
  color: var(--pm-text-secondary);
}

.pm-recommendation-box {
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: var(--pm-radius);
  padding: 0.65rem 0.85rem;
  font-size: 0.825rem;
  color: #0369a1;
}

/* Tabs */
.pm-tabs-card {
  padding: 0;
}

.pm-tabs-header {
  display: flex;
  border-bottom: 1px solid var(--pm-border);
  background-color: var(--pm-bg-subtle);
  overflow-x: auto;
}

.pm-tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.85rem 1.25rem;
  font-size: 0.825rem;
  font-weight: 500;
  color: var(--pm-text-secondary);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
}

.pm-tab-btn:hover {
  color: var(--pm-text-primary);
}

.pm-tab-btn.active {
  color: var(--pm-primary);
  background-color: #ffffff;
  border-bottom-color: var(--pm-primary);
  font-weight: 600;
}

.pm-tab-body {
  padding: 1.25rem;
}

.pm-section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.pm-section-title {
  font-size: 0.9rem;
  font-weight: 600;
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
  max-height: 90vh;
  overflow-y: auto;
}

.pm-ack-modal {
  max-width: 680px;
}

.pm-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--pm-border);
}

.pm-modal-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pm-modal-close {
  background: none;
  border: none;
  color: var(--pm-text-muted);
  cursor: pointer;
}

.pm-ack-content {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.pm-ack-title {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--pm-text-secondary);
  margin-bottom: 0.4rem;
}

.pm-ack-text {
  font-size: 0.9rem;
  line-height: 1.4;
  color: var(--pm-text-primary);
}

.pm-ack-evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.5rem;
}

.pm-ack-evidence-card {
  background: var(--pm-bg-subtle);
  border: 1px solid var(--pm-border);
  border-radius: var(--pm-radius);
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
}

.pm-ack-evidence-label {
  font-size: 0.7rem;
  color: var(--pm-text-muted);
}

.pm-ack-evidence-val {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--pm-text-primary);
}

.pm-ack-rec-box {
  background-color: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: var(--pm-radius);
  padding: 0.85rem;
}

.pm-ack-override {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: var(--pm-critical-text);
  background-color: var(--pm-critical-bg);
  padding: 0.65rem;
  border-radius: var(--pm-radius);
}

.pm-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--pm-border);
}

.pm-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
