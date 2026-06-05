import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',          name: 'Login',           component: () => import('../views/LoginView.vue') },
  { path: '/dashboard', name: 'Dashboard',        component: () => import('../views/DashboardView.vue'), meta: { requiresAuth: true } },
  { path: '/patients',  name: 'Patients',         component: () => import('../views/PatientsView.vue'),  meta: { requiresAuth: true } },
  { path: '/assessment/new', name: 'NewAssessment', component: () => import('../views/NewAssessmentView.vue'), meta: { requiresAuth: true } },
  { path: '/assessment/:id/result', name: 'AIResult', component: () => import('../views/AIResultView.vue'), meta: { requiresAuth: true } },
  { path: '/assessment/:id/measures', name: 'Measures', component: () => import('../views/MeasuresView.vue'), meta: { requiresAuth: true } },
  { path: '/sos',       name: 'SOS',              component: () => import('../views/SOSView.vue'),       meta: { requiresAuth: true } },
  { path: '/reports',   name: 'Reports',          component: () => import('../views/ReportsView.vue'),   meta: { requiresAuth: true } },
  { path: '/users',     name: 'Users',            component: () => import('../views/UsersView.vue'),     meta: { requiresAuth: true } },
  { path: '/settings',  name: 'Settings',         component: () => import('../views/SettingsView.vue'),  meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const isLoggedIn = !!localStorage.getItem('exobios_auth')
  if (to.meta.requiresAuth && !isLoggedIn) return { name: 'Login' }
  if (to.name === 'Login' && isLoggedIn) return { name: 'Dashboard' }
})

export default router
