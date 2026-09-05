import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/persona',
    },
    {
      path: '/dashboard',
      redirect: '/persona',
    },
    {
      path: '/resume',
      name: 'resume',
      component: () => import('../views/ResumeAnalysis.vue'),
    },
    {
      path: '/matching',
      name: 'matching',
      component: () => import('../views/JobMatching.vue'),
    },
    {
      path: '/interview',
      name: 'interview',
      component: () => import('../views/InterviewSimulator.vue'),
    },
    {
      path: '/persona',
      name: 'persona',
      component: () => import('../views/JobPersona.vue'),
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
    },
    {
      path: '/position-def',
      name: 'position-def',
      component: () => import('../views/PositionDefinition.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { layout: 'auth', public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { layout: 'auth', public: true },
    },
  ],
})


router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const isPublic = to.meta.public === true

  if (!token && !isPublic) {

    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (token && isPublic) {

    next('/persona')
  } else {
    next()
  }
})

export default router
