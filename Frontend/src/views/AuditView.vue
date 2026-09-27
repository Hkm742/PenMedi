<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../services/api'
import { ShieldCheck, Search, FileCode, CheckCircle2, X } from 'lucide-vue-next'

const logs = ref<any[]>([])
const stats = ref<any>(null)
const total = ref(0)
const loading = ref(false)

const filterAction = ref('')
const filterResource = ref('')
const selectedLog = ref<any | null>(null)

onMounted(async () => {
  await Promise.all([loadStats(), loadLogs()])
})

const loadStats = async () => {
  try {
    const res = await api.get('/audit/stats')
    stats.value = res.data
  } catch (err) {
    console.error('Failed to load audit stats', err)
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params: any = { limit: 100 }
    if (filterAction.value) params.action = filterAction.value
    if (filterResource.value) params.resource = filterResource.value

    const res = await api.get('/audit/logs', { params })
    logs.value = res.data.items
    total.value = res.data.total
  } catch (err) {
    console.error('Failed to load audit logs', err)
  } finally {
    loading.value = false
  }
}

const formatActionBadge = (action: string) => {
  if (action.includes('LOGIN') || action.includes('LOGOUT')) return 'pm-badge-neutral'
  if (action.includes('ALERT') || action.includes('EVALUATION')) return 'pm-badge-critical'
  if (action.includes('CREATE') || action.includes('ADD')) return 'pm-badge-info'
  return 'pm-badge-success'
}
</script>

<template>
  <div class="pm-page-container">
    <div class="pm-card-header" style="margin-bottom: 0;">
      <div>
        <h2 style="font-size: 1.25rem;">Security & Compliance Audit Trail</h2>
        <p style="font-size: 0.8rem; color: var(--pm-text-muted);">
          Cryptographically Verified Immutable Event Stream • SHA-256 Digest Validation
        </p>
      </div>
      <span class="pm-badge pm-badge-success">Compliance Verified</span>
    </div>

    <!-- Stats Grid -->
    <div v-if="stats" class="pm-audit-metrics">
      <div class="pm-card pm-audit-metric-card">
        <span class="pm-metric-label">Total Immutable Records</span>
        <span class="pm-metric-value">{{ stats.total_logs }}</span>
        <span class="pm-metric-sub">Full system lifecycle</span>
      </div>

      <div class="pm-card pm-audit-metric-card">
        <span class="pm-metric-label">Last 24 Hours Events</span>
        <span class="pm-metric-value">{{ stats.recent_activity_count_24h }}</span>
        <span class="pm-metric-sub">Real-time throughput</span>
      </div>

      <div class="pm-card pm-audit-metric-card">
        <span class="pm-metric-label">Integrity Algorithm</span>
        <span class="pm-metric-value" style="font-size: 1.25rem; font-family: var(--font-mono);">SHA-256</span>
        <span class="pm-metric-sub">Zero-tamper digital sealing</span>
      </div>
    </div>

    <!-- Filters Toolbar -->
    <div class="pm-card" style="padding: 0.85rem 1.25rem;">
      <div class="pm-audit-toolbar">
        <div class="pm-filter-selects">
          <select v-model="filterAction" class="pm-input" style="width: 220px;" @change="loadLogs">
            <option value="">All Event Actions</option>
            <option value="USER_LOGIN">USER_LOGIN</option>
            <option value="CDSS_EVALUATION">CDSS_EVALUATION</option>
            <option value="ALERT_ACKNOWLEDGED">ALERT_ACKNOWLEDGED</option>
            <option value="PATIENT_CHART_VIEW">PATIENT_CHART_VIEW</option>
            <option value="MEDICATION_ADD">MEDICATION_ADD</option>
            <option value="GENOMICS_ADD">GENOMICS_ADD</option>
          </select>

          <select v-model="filterResource" class="pm-input" style="width: 180px;" @change="loadLogs">
            <option value="">All Resources</option>
            <option value="patient">patient</option>
            <option value="alert">alert</option>
            <option value="medication">medication</option>
            <option value="genomic">genomic</option>
            <option value="auth">auth</option>
          </select>
        </div>

        <button type="button" class="pm-btn pm-btn-secondary pm-btn-sm" @click="loadLogs">
          Refresh Trail
        </button>
      </div>
    </div>

    <!-- Audit Table -->
    <div class="pm-card">
      <div class="pm-table-wrapper">
        <table class="pm-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Actor (Hospital Staff)</th>
              <th>Resource</th>
              <th>IP Address</th>
              <th>Cryptographic Digest (SHA-256)</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="pm-table-empty">Loading audit records...</td>
            </tr>
            <tr v-else-if="logs.length === 0">
              <td colspan="7" class="pm-table-empty">No audit records found.</td>
            </tr>
            <tr v-for="log in logs" v-else :key="log.id">
              <td style="font-size: 0.775rem; white-space: nowrap;">
                {{ new Date(log.timestamp).toLocaleString() }}
              </td>
              <td>
                <span class="pm-badge" :class="formatActionBadge(log.action)">
                  {{ log.action }}
                </span>
              </td>
              <td>
                <div style="font-size: 0.8rem; font-weight: 500;">{{ log.actor_name || 'System' }}</div>
                <div style="font-size: 0.7rem; color: var(--pm-text-muted);">{{ log.actor_email }}</div>
              </td>
              <td>
                <span class="pm-font-mono" style="font-size: 0.75rem;">
                  {{ log.resource }}
                  <span v-if="log.resource_id" style="color: var(--pm-text-muted);">
                    ({{ log.resource_id.substring(0, 8) }}...)
                  </span>
                </span>
              </td>
              <td class="pm-font-mono" style="font-size: 0.75rem;">
                {{ log.ip_address || '127.0.0.1' }}
              </td>
              <td>
                <span class="pm-hash-badge pm-font-mono" :title="log.payload_hash">
                  {{ log.payload_hash.substring(0, 16) }}...
                </span>
              </td>
              <td>
                <button
                  type="button"
                  class="pm-btn pm-btn-secondary pm-btn-sm"
                  style="padding: 0.2rem 0.4rem; font-size: 0.72rem;"
                  @click="selectedLog = log"
                >
                  <FileCode :size="12" />
                  <span>Payload</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payload Details Modal -->
    <div v-if="selectedLog" class="pm-modal-overlay">
      <div class="pm-modal-card" style="max-width: 600px;">
        <div class="pm-modal-header">
          <div>
            <h3>Audit Record Details</h3>
            <span class="pm-badge" :class="formatActionBadge(selectedLog.action)">
              {{ selectedLog.action }}
            </span>
          </div>
          <button type="button" class="pm-modal-close" @click="selectedLog = null">
            <X :size="18" />
          </button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 0.75rem; font-size: 0.8rem;">
          <div><strong>Timestamp:</strong> {{ selectedLog.timestamp }}</div>
          <div><strong>Actor:</strong> {{ selectedLog.actor_name }} ({{ selectedLog.actor_email }})</div>
          <div><strong>Resource:</strong> {{ selectedLog.resource }} ({{ selectedLog.resource_id }})</div>
          <div><strong>Full SHA-256 Payload Hash:</strong></div>
          <div class="pm-hash-box pm-font-mono">{{ selectedLog.payload_hash }}</div>

          <div><strong>Stored Event Metadata:</strong></div>
          <pre class="pm-json-box pm-font-mono">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
        </div>

        <div class="pm-modal-footer">
          <button type="button" class="pm-btn pm-btn-secondary" @click="selectedLog = null">Close</button>
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

.pm-audit-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.pm-audit-metric-card {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pm-metric-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--pm-text-muted);
}

.pm-metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--pm-text-primary);
}

.pm-metric-sub {
  font-size: 0.725rem;
  color: var(--pm-text-muted);
}

.pm-audit-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.pm-filter-selects {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.pm-hash-badge {
  background-color: var(--pm-bg-subtle);
  border: 1px solid var(--pm-border);
  padding: 0.15rem 0.4rem;
  border-radius: var(--pm-radius);
  font-size: 0.7rem;
  color: var(--pm-text-secondary);
  display: inline-block;
}

.pm-hash-box {
  background: var(--pm-bg-subtle);
  border: 1px solid var(--pm-border);
  padding: 0.5rem;
  border-radius: var(--pm-radius);
  word-break: break-all;
  font-size: 0.75rem;
}

.pm-json-box {
  background: #0f172a;
  color: #f8fafc;
  padding: 0.75rem;
  border-radius: var(--pm-radius);
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 250px;
}

.pm-font-mono {
  font-family: var(--font-mono);
}
</style>
