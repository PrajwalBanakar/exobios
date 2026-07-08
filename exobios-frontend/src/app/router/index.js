import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/features/auth/stores/auth'

/**
 * All route definitions.
 * Views are lazy-loaded so each feature chunk is only downloaded when needed.
 * Routes with `meta.requiresAuth: true` are guarded by the beforeEach hook below.
 */
const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('@/features/auth/views/LoginView.vue'),
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/features/dashboard/views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients',
    name: 'Patients',
    component: () => import('@/features/patients/views/PatientsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients/new',
    name: 'AddPatient',
    component: () => import('@/features/patients/views/AddPatientView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients/:id/edit',
    name: 'EditPatient',
    component: () => import('@/features/patients/views/AddPatientView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/patients/:id',
    name: 'PatientDetail',
    component: () => import('@/features/patients/views/PatientDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assessment/new',
    name: 'NewAssessment',
    component: () => import('@/features/assessments/views/NewAssessmentView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assessment/:id/edit',
    name: 'EditAssessment',
    component: () => import('@/features/assessments/views/NewAssessmentView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assessment/:id/result',
    name: 'AIResult',
    component: () => import('@/features/assessments/views/AIResultView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assessment/:id/analysis',
    name: 'FullAnalysis',
    component: () => import('@/features/assessments/views/FullAnalysisView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/assessment/:id/measures',
    name: 'Measures',
    component: () => import('@/features/measures/views/MeasuresView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/sos',
    name: 'SOS',
    component: () => import('@/features/sos/views/SOSView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/features/reports/views/ReportsView.vue'),
    meta: { requiresAuth: true, permission: 'view_reports' },
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/features/admin/views/UsersView.vue'),
    meta: { requiresAuth: true, permission: 'manage_users' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/features/settings/views/SettingsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/features/notifications/views/NotificationsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/system-updates',
    name: 'SystemUpdates',
    component: () => import('@/features/notifications/views/SystemUpdatesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/features/settings/views/ProfileView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/referrals',
    name: 'Referrals',
    component: () => import('@/features/referrals/views/ReferralsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/teleconsult',
    name: 'Teleconsult',
    component: () => import('@/features/teleconsult/views/TeleconsultView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('@/features/devices/views/DeviceView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/feedback',
    name: 'Feedback',
    component: () => import('@/features/feedback/views/FeedbackView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'SuperAdmin',
    component: () => import('@/features/admin/views/SuperAdminView.vue'),
    meta: { requiresAuth: true, permission: 'super_admin' },
  },
  {
    path: '/child-health',
    name: 'ChildHealth',
    component: () => import('@/pages/ComingSoonView.vue'),
    meta: { requiresAuth: true, title: 'Child Health' },
  },
  {
    path: '/maternal-health',
    name: 'MaternalHealth',
    component: () => import('@/pages/ComingSoonView.vue'),
    meta: { requiresAuth: true, title: 'Maternal Health' },
  },
  {
    path: '/unauthorized',
    name: 'Unauthorized',
    component: () => import('@/pages/UnauthorizedView.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Auth guard: redirect unauthenticated or expired sessions to login
router.beforeEach((to) => {
  let session = null
  try {
    const raw = localStorage.getItem('exobios_auth')
    if (raw) {
      session = JSON.parse(raw)
      if (Date.now() > (session?.expiresAt ?? 0)) {
        localStorage.removeItem('exobios_auth')
        session = null
      }
    }
  } catch { session = null }

  const isLoggedIn = !!session
  if (to.meta.requiresAuth && !isLoggedIn) return { name: 'Login' }
  if (to.name === 'Login' && isLoggedIn) return { name: 'Dashboard' }

  // Route-level permission gate — the sidebar already hides these links from users
  // without the permission, but the route itself must enforce it too (otherwise a
  // Paramedic/Doctor could reach /admin or /users by typing the URL directly).
  if (to.meta.permission && isLoggedIn) {
    const auth = useAuthStore()
    if (!auth.hasPermission(to.meta.permission)) return { name: 'Unauthorized' }
  }
})

export default router
