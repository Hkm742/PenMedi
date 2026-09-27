<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useClinicalStore, type CDSSRule } from '../stores/clinical'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'
import { BookOpen, ShieldCheck, Plus, X, Search } from 'lucide-vue-next'

const clinicalStore = useClinicalStore()
const authStore = useAuthStore()

const filterSeverity = ref('ALL')
const searchFilter = ref('')
const showNewRuleModal = ref(false)
const selectedRule = ref<CDSSRule | null>(null)

onMounted(async () => {
  await clinicalStore.fetchRules()
})

const filteredRules = computed(() => {
  return clinicalStore.rules.filter(r => {
    const matchesSev = filterSeverity.value === 'ALL' || r.severity === filterSeverity.value
    const matchesQuery =
      !searchFilter.value ||
      r.rule_code.toLowerCase().includes(searchFilter.value.toLowerCase()) ||
      r.description.toLowerCase().includes(searchFilter.value.toLowerCase()) ||
      (r.condition_expression?.drugs || []).some((d: string) => d.toLowerCase().includes(searchFilter.value.toLowerCase()))
    return matchesSev && matchesQuery
  })
})
</script>

<template>
  <div class="pm-page-container">
    <div class="pm-card-header" style="margin-bottom: 0;">
      <div>
        <h2 style="font-size: 1.25rem;">Pharmacogenomic Decision Support Rules</h2>
        <p style="font-size: 0.8rem; color: var(--pm-text-muted);">
          Institutional Rule Registry • CPIC & DPWG Guidelines adapted for Levy Mwanawasa Teaching Hospital
        </p>
      </div>
      <span class="pm-badge pm-badge-info">Deterministic & Traceable</span>
    </div>

    <!-- Filters Toolbar -->
    <div class="pm-card" style="padding: 0.85rem 1.25rem;">
      <div class="pm-rule-toolbar">
        <div class="pm-search-box">
          <Search :size="16" class="pm-search-icon" />
          <input
            v-model="searchFilter"
            type="text"
            placeholder="Search rules by drug, gene, or code..."
            class="pm-input pm-search-input"
          />
        </div>

        <div class="pm-filter-group">
          <span style="font-size: 0.8rem; color: var(--pm-text-muted);">Severity:</span>
          <button
            type="button"
            class="pm-filter-pill"
            :class="{ active: filterSeverity === 'ALL' }"
            @click="filterSeverity = 'ALL'"
          >
            All
          </button>
          <button
            type="button"
            class="pm-filter-pill critical"
            :class="{ active: filterSeverity === 'CRITICAL' }"
            @click="filterSeverity = 'CRITICAL'"
          >
            Critical
          </button>
          <button
            type="button"
            class="pm-filter-pill warning"
            :class="{ active: filterSeverity === 'WARNING' }"
            @click="filterSeverity = 'WARNING'"
          >
            Warning
          </button>
        </div>
      </div>
    </div>

    <!-- Rules Grid -->
    <div class="pm-rules-grid">
      <div
        v-for="rule in filteredRules"
        :key="rule.id"
        class="pm-card pm-rule-card"
        :class="rule.severity.toLowerCase()"
        @click="selectedRule = rule"
      >
        <div class="pm-rule-card-top">
          <span
            class="pm-badge"
            :class="rule.severity === 'CRITICAL' ? 'pm-badge-critical' : 'pm-badge-warning'"
          >
            {{ rule.severity }}
          </span>
          <span class="pm-font-mono pm-text-muted" style="font-size: 0.75rem;">
            {{ rule.rule_code }}
          </span>
        </div>

        <div class="pm-rule-drugs">
          <span class="pm-rule-tag">Target: {{ (rule.condition_expression?.drugs || []).join(', ') }}</span>
          <span class="pm-rule-tag gene">Gene: {{ rule.condition_expression?.gene }}</span>
        </div>

        <p class="pm-rule-desc">{{ rule.description }}</p>

        <div class="pm-rule-rec">
          <strong>Guideline Action:</strong> {{ rule.recommendation }}
        </div>

        <div class="pm-rule-citation">
          <strong>Reference:</strong> {{ rule.clinical_reference }}
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

.pm-rule-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.pm-search-box {
  display: flex;
  align-items: center;
  position: relative;
  flex: 1;
  max-width: 420px;
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

.pm-filter-group {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.pm-filter-pill {
  border: 1px solid var(--pm-border);
  background: none;
  font-size: 0.775rem;
  font-weight: 500;
  padding: 0.25rem 0.65rem;
  border-radius: var(--pm-radius);
  cursor: pointer;
  color: var(--pm-text-secondary);
}

.pm-filter-pill.active {
  background-color: var(--pm-primary);
  border-color: var(--pm-primary);
  color: #ffffff;
}

.pm-filter-pill.critical.active {
  background-color: var(--pm-critical-border);
  border-color: var(--pm-critical-border);
  color: #ffffff;
}

.pm-filter-pill.warning.active {
  background-color: var(--pm-warning-border);
  border-color: var(--pm-warning-border);
  color: #ffffff;
}

.pm-rules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 1.25rem;
}

.pm-rule-card {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border-left: 4px solid var(--pm-border);
}

.pm-rule-card.critical {
  border-left-color: var(--pm-critical-border);
}

.pm-rule-card.warning {
  border-left-color: var(--pm-warning-border);
}

.pm-rule-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pm-rule-drugs {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.pm-rule-tag {
  background: var(--pm-bg-subtle);
  border: 1px solid var(--pm-border);
  padding: 0.2rem 0.5rem;
  border-radius: var(--pm-radius);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--pm-text-secondary);
}

.pm-rule-tag.gene {
  background: var(--pm-primary-light);
  border-color: #bae6fd;
  color: var(--pm-primary);
}

.pm-rule-desc {
  font-size: 0.85rem;
  color: var(--pm-text-primary);
  line-height: 1.4;
}

.pm-rule-rec {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: var(--pm-radius);
  padding: 0.65rem;
  font-size: 0.8rem;
  color: #0369a1;
  line-height: 1.35;
}

.pm-rule-citation {
  font-size: 0.725rem;
  color: var(--pm-text-muted);
  border-top: 1px solid var(--pm-border);
  padding-top: 0.5rem;
}
</style>
