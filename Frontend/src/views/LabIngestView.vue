<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useClinicalStore } from '../stores/clinical'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'
import { Dna, Plus, CheckCircle2, ShieldAlert } from 'lucide-vue-next'

const clinicalStore = useClinicalStore()
const authStore = useAuthStore()

const allGenomics = ref<any[]>([])
const loading = ref(false)
const submitting = ref(false)
const successMsg = ref<string | null>(null)
const errorMsg = ref<string | null>(null)

const form = ref({
  patient_id: '',
  gene_symbol: 'CYP2C19',
  variant_allele: '*2/*2',
  phenotype: 'Poor Metabolizer',
  test_date: new Date().toISOString().split('T')[0],
})

const genePresets: Record<string, { alleles: string[]; phenotypes: string[] }> = {
  CYP2C19: {
    alleles: ['*1/*1', '*1/*2', '*2/*2', '*2/*3', '*1/*17', '*17/*17'],
    phenotypes: ['Normal Metabolizer', 'Intermediate Metabolizer', 'Poor Metabolizer', 'Ultra-Rapid Metabolizer'],
  },
  'HLA-B': {
    alleles: ['*57:01 (Positive)', '*57:01 (Negative)', '*58:01 (Positive)', '*58:01 (Negative)'],
    phenotypes: ['Hypersensitivity Risk', 'Normal / Low Risk', 'SCAR / SJS Risk'],
  },
  CYP2D6: {
    alleles: ['*1/*1', '*1/*4', '*4/*4', '*1xN/*1 (Gene Duplication)', '*5/*5'],
    phenotypes: ['Normal Metabolizer', 'Intermediate Metabolizer', 'Poor Metabolizer', 'Ultra-Rapid Metabolizer'],
  },
  TPMT: {
    alleles: ['*1/*1', '*1/*3A', '*3A/*3A', '*1/*3C'],
    phenotypes: ['Normal Metabolizer', 'Intermediate Metabolizer', 'Poor Metabolizer'],
  },
  VKORC1: {
    alleles: ['-1639G>G (GG)', '-1639G>A (GA)', '-1639G>A (AA)'],
    phenotypes: ['Normal Sensitivity', 'Intermediate Sensitivity', 'High Sensitivity'],
  },
  DPYD: {
    alleles: ['*1/*1', '*2A/*1', '*2A/*2A', '*13/*1'],
    phenotypes: ['Normal Metabolizer', 'Intermediate Metabolizer', 'Poor Metabolizer'],
  },
}

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  loading.value = true
  try {
    await clinicalStore.fetchPatients()
    if (clinicalStore.patients.length > 0 && !form.value.patient_id) {
      form.value.patient_id = clinicalStore.patients[0]?.id || ''
    }
    const res = await api.get('/genomics')
    allGenomics.value = res.data
  } catch (err: any) {
    console.error('Failed to load lab data', err)
  } finally {
    loading.value = false
  }
}

const onGeneChange = () => {
  const preset = genePresets[form.value.gene_symbol]
  if (preset && preset.alleles[0] && preset.phenotypes[0]) {
    form.value.variant_allele = preset.alleles[0]
    form.value.phenotype = preset.phenotypes[0]
  }
}

const handleSubmit = async () => {
  if (!form.value.patient_id) {
    errorMsg.value = 'Please select a patient'
    return
  }
  submitting.value = true
  successMsg.value = null
  errorMsg.value = null
  try {
    await api.post(`/patients/${form.value.patient_id}/genomics`, {
      gene_symbol: form.value.gene_symbol,
      variant_allele: form.value.variant_allele,
      phenotype: form.value.phenotype,
      test_date: form.value.test_date,
    })
    successMsg.value = `Verified genomic test for ${form.value.gene_symbol} saved successfully and CDSS evaluated!`
    await loadData()
  } catch (err: any) {
    errorMsg.value = err.response?.data?.detail || 'Failed to submit genomic record'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="pm-page-container">
    <div class="pm-card-header" style="margin-bottom: 0;">
      <div>
        <h2 style="font-size: 1.25rem;">Pharmacogenomic Laboratory Ingestion</h2>
        <p style="font-size: 0.8rem; color: var(--pm-text-muted);">
          Authorized Lab Officer Portal • Levy Mwanawasa Teaching Hospital Molecular Genetics Unit
        </p>
      </div>
      <span class="pm-badge pm-badge-warning">Lab_Officer Clearance</span>
    </div>

    <!-- Feedback Banners -->
    <div v-if="successMsg" class="pm-alert-banner success">
      <CheckCircle2 :size="16" />
      <span>{{ successMsg }}</span>
    </div>
    <div v-if="errorMsg" class="pm-alert-banner critical">
      <ShieldAlert :size="16" />
      <span>{{ errorMsg }}</span>
    </div>

    <div class="pm-lab-grid">
      <!-- Ingestion Form -->
      <div class="pm-card">
        <h3 style="font-size: 0.95rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--pm-border);">
          Ingest Genetic Test Result
        </h3>

        <form @submit.prevent="handleSubmit" class="pm-lab-form">
          <div class="pm-form-group">
            <label class="pm-form-label">Select Patient *</label>
            <select v-model="form.patient_id" class="pm-input" required>
              <option v-for="p in clinicalStore.patients" :key="p.id" :value="p.id">
                {{ p.medical_record_number }} — {{ p.first_name }} {{ p.last_name }}
              </option>
            </select>
          </div>

          <div class="pm-form-group">
            <label class="pm-form-label">Target Gene Symbol *</label>
            <select v-model="form.gene_symbol" class="pm-input" @change="onGeneChange">
              <option value="CYP2C19">CYP2C19 (Clopidogrel / Plavix metabolism)</option>
              <option value="HLA-B">HLA-B (Abacavir / Allopurinol hypersensitivity)</option>
              <option value="CYP2D6">CYP2D6 (Codeine / Tamoxifen metabolism)</option>
              <option value="TPMT">TPMT (Azathioprine myelosuppression risk)</option>
              <option value="VKORC1">VKORC1 (Warfarin dosing sensitivity)</option>
              <option value="DPYD">DPYD (5-FU fluoropyrimidine toxicity)</option>
            </select>
          </div>

          <div class="pm-form-row">
            <div class="pm-form-group">
              <label class="pm-form-label">Variant / Allele Result *</label>
              <input
                v-model="form.variant_allele"
                type="text"
                required
                placeholder="e.g. *2/*2"
                class="pm-input pm-font-mono"
              />
            </div>
            <div class="pm-form-group">
              <label class="pm-form-label">Metabolizer Phenotype *</label>
              <input
                v-model="form.phenotype"
                type="text"
                required
                placeholder="e.g. Poor Metabolizer"
                class="pm-input"
              />
            </div>
          </div>

          <div class="pm-form-group">
            <label class="pm-form-label">Sequencing / Test Date *</label>
            <input v-model="form.test_date" type="date" required class="pm-input" />
          </div>

          <button
            type="submit"
            class="pm-btn pm-btn-primary"
            style="margin-top: 0.5rem;"
            :disabled="submitting"
          >
            <Dna :size="16" />
            <span>{{ submitting ? 'Submitting & Signing...' : 'Verify & Submit Test Result' }}</span>
          </button>
        </form>
      </div>

      <!-- Recent Laboratory Records -->
      <div class="pm-card">
        <h3 style="font-size: 0.95rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--pm-border);">
          Recent Institutional Biomarker Logs
        </h3>

        <div class="pm-table-wrapper">
          <table class="pm-table">
            <thead>
              <tr>
                <th>Gene</th>
                <th>Allele</th>
                <th>Phenotype</th>
                <th>Test Date</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="allGenomics.length === 0">
                <td colspan="4" class="pm-table-empty">No genomic records ingested yet.</td>
              </tr>
              <tr v-for="rec in allGenomics" v-else :key="rec.id">
                <td class="pm-font-mono pm-text-bold">{{ rec.gene_symbol }}</td>
                <td class="pm-font-mono">{{ rec.variant_allele }}</td>
                <td>
                  <span
                    class="pm-badge"
                    :class="rec.phenotype.includes('Poor') || rec.phenotype.includes('Risk') ? 'pm-badge-critical' : 'pm-badge-info'"
                  >
                    {{ rec.phenotype }}
                  </span>
                </td>
                <td>{{ rec.test_date }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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

.pm-lab-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 1.25rem;
}

.pm-lab-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pm-form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
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

.pm-font-mono {
  font-family: var(--font-mono);
}

.pm-text-bold {
  font-weight: 600;
}

@media (max-width: 900px) {
  .pm-lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>
