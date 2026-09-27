import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['Clinician', 'Administrator', 'Lab_Officer'] },
  },
  {
    path: '/patients/:id',
    name: 'patient-detail',
    component: () => import('../views/PatientDetailView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['Clinician', 'Administrator', 'Lab_Officer'] },
  },
  {
    path: '/lab-ingest',
    name: 'lab-ingest',
    component: () => import('../views/LabIngestView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['Lab_Officer', 'Administrator'] },
  },
  {
    path: '/rules',
    name: 'rules',
    component: () => import('../views/RuleEngineView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/audit',
    name: 'audit',
    component: () => import('../views/AuditView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['Auditor', 'Administrator'] },
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/UserManagementView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['Administrator'] },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // If public route (e.g. login)
  if (to.meta.public) {
    if (authStore.isAuthenticated) {
      if (authStore.isAuditor) return next('/audit')
      if (authStore.isLabOfficer) return next('/lab-ingest')
      return next('/')
    }
    return next()
  }

  // Protected routes
  if (!authStore.isAuthenticated) {
    return next('/login')
  }

  // RBAC Role Authorization check
  const allowedRoles = to.meta.allowedRoles as string[] | undefined
  if (allowedRoles && !allowedRoles.includes(authStore.userRole)) {
    // Redirect based on current role
    if (authStore.isAuditor) return next('/audit')
    if (authStore.isLabOfficer) return next('/lab-ingest')
    return next('/')
  }

  next()
})

export default router
