import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../services/api'

export interface Patient {
  id: string
  medical_record_number: string
  first_name: string
  last_name: string
  dob: string
  sex: string
  contact_info?: Record<string, any>
  created_at: string
  active_alerts_count?: number
}

export interface Diagnosis {
  id: string
  patient_id: string
  icd10_code: string
  description: string
  date_diagnosed: string
  clinician_id?: string
}

export interface Medication {
  id: string
  patient_id: string
  drug_name: string
  dosage: string
  frequency: string
  start_date: string
  end_date?: string
  active: boolean
}

export interface GenomicRecord {
  id: string
  patient_id: string
  gene_symbol: string
  variant_allele: string
  phenotype: string
  test_date: string
  verified_by_id?: string
}

export interface CDSSRule {
  id: string
  rule_code: string
  description: string
  condition_expression: Record<string, any>
  severity: 'CRITICAL' | 'WARNING' | 'INFORMATIONAL'
  recommendation: string
  clinical_reference: string
}

export interface AlertInstance {
  id: string
  patient_id: string
  rule_id: string
  severity: 'CRITICAL' | 'WARNING' | 'INFORMATIONAL'
  message: string
  evidence_data?: Record<string, any>
  triggered_at: string
  acknowledged_by_id?: string
  acknowledged_at?: string
  clinician_note?: string
  status: 'TRIGGERED' | 'ACKNOWLEDGED' | 'OVERRIDDEN'
  rule?: CDSSRule
}

export interface PatientDetail extends Patient {
  diagnoses: Diagnosis[]
  medications: Medication[]
  genomic_records: GenomicRecord[]
  alerts: AlertInstance[]
}

export const useClinicalStore = defineStore('clinical', () => {
  const patients = ref<Patient[]>([])
  const totalPatients = ref(0)
  const currentPatient = ref<PatientDetail | null>(null)
  const rules = ref<CDSSRule[]>([])
  const loading = ref(false)
  const evaluating = ref(false)
  const error = ref<string | null>(null)

  async function fetchPatients(search: string = '', limit = 50, offset = 0) {
    loading.value = true
    error.value = null
    try {
      const params: any = { limit, offset }
      if (search.trim()) params.search = search.trim()
      const response = await api.get('/patients', { params })
      patients.value = response.data.items
      totalPatients.value = response.data.total
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load patients'
    } finally {
      loading.value = false
    }
  }

  async function fetchPatientDetail(patientId: string) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/patients/${patientId}`)
      currentPatient.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load patient record'
      return null
    } finally {
      loading.value = false
    }
  }

  async function createPatient(data: {
    medical_record_number: string
    first_name: string
    last_name: string
    dob: string
    sex: string
    contact_info?: Record<string, any>
  }) {
    loading.value = true
    error.value = null
    try {
      const response = await api.post('/patients', data)
      await fetchPatients()
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to register patient'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addDiagnosis(patientId: string, data: { icd10_code: string; description: string; date_diagnosed: string }) {
    const response = await api.post(`/patients/${patientId}/diagnoses`, data)
    if (currentPatient.value && currentPatient.value.id === patientId) {
      await fetchPatientDetail(patientId)
    }
    return response.data
  }

  async function addMedication(patientId: string, data: { drug_name: string; dosage: string; frequency: string; start_date: string; active?: boolean }) {
    const response = await api.post(`/patients/${patientId}/medications`, data)
    if (currentPatient.value && currentPatient.value.id === patientId) {
      await fetchPatientDetail(patientId)
    }
    return response.data
  }

  async function addGenomicRecord(patientId: string, data: { gene_symbol: string; variant_allele: string; phenotype: string; test_date: string }) {
    const response = await api.post(`/patients/${patientId}/genomics`, data)
    if (currentPatient.value && currentPatient.value.id === patientId) {
      await fetchPatientDetail(patientId)
    }
    return response.data
  }

  async function evaluatePatientCDSS(patientId: string) {
    evaluating.value = true
    error.value = null
    try {
      const response = await api.post(`/cdss/evaluate/${patientId}`)
      if (currentPatient.value && currentPatient.value.id === patientId) {
        await fetchPatientDetail(patientId)
      }
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Evaluation failed'
      throw err
    } finally {
      evaluating.value = false
    }
  }

  async function acknowledgeAlert(alertId: string, note: string, override: boolean = false) {
    const response = await api.post(`/cdss/alerts/${alertId}/acknowledge`, {
      clinician_note: note,
      override,
    })
    if (currentPatient.value) {
      await fetchPatientDetail(currentPatient.value.id)
    }
    return response.data
  }

  async function fetchRules() {
    try {
      const response = await api.get('/cdss/rules')
      rules.value = response.data
    } catch (err: any) {
      console.error('Failed to load rules', err)
    }
  }

  return {
    patients,
    totalPatients,
    currentPatient,
    rules,
    loading,
    evaluating,
    error,
    fetchPatients,
    fetchPatientDetail,
    createPatient,
    addDiagnosis,
    addMedication,
    addGenomicRecord,
    evaluatePatientCDSS,
    acknowledgeAlert,
    fetchRules,
  }
})
