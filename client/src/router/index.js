import { createRouter, createWebHistory } from 'vue-router'

import UsersView from '@/views/UsersView.vue'
import MembershipsView from '@/views/MembershipsView.vue'
import MembershipTypesView from '@/views/MembershipTypesView.vue'
import WorkoutSessionsView from '@/views/WorkoutSessionsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/users', // по умолчанию открывать пользователей
    },
    {
      path: '/users',
      name: 'UsersView',
      component: UsersView,
      props: route => ({ role: route.query.role || '' }) // позволяет фильтровать по роли
    },
    {
      path: '/memberships',
      name: 'MembershipsView',
      component: MembershipsView
    },
    {
      path: '/membershiptypes',
      name: 'MembershipTypesView',
      component: MembershipTypesView
    },
    {
      path: '/workoutsessions',
      name: 'WorkoutSessionsView',
      component: WorkoutSessionsView
    }
  ]
})

export default router
