import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

import UsersView from "@/views/UsersView.vue"
import MembershipsView from "@/views/MembershipsView.vue"
import MembershipTypesView from "@/views/MembershipTypesView.vue"
import WorkoutSessionsView from "@/views/WorkoutSessionsView.vue"
import LoginView from "@/views/LoginView.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // страница логина
    {
      path: "/login",
      name: "LoginView",
      component: LoginView,
    },

    // по умолчанию редиректим на пользователей
    {
      path: "/",
      redirect: "/users",
    },
    {
      path: "/users",
      name: "UsersView",
      component: UsersView,
      props: route => ({ role: route.query.role || "" }),
    },
    {
      path: "/memberships",
      name: "MembershipsView",
      component: MembershipsView,
    },
    {
      path: "/membershiptypes",
      name: "MembershipTypesView",
      component: MembershipTypesView,
    },
    {
      path: "/workoutsessions",
      name: "WorkoutSessionsView",
      component: WorkoutSessionsView,
    },
  ],
})

/**
 * Глобальный guard:
 *  - на /login всегда пускаем (если уже залогинен — редирект на UsersView)
 *  - на любые другие страницы пускаем только если пользователь авторизован
 */
router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  // если идём на логин
  if (to.name === "LoginView") {
    // если уже авторизованы — нет смысла показывать форму логина
    if (auth.isAuthenticated) {
      return next({ name: "UsersView" })
    }
    return next()
  }

  // Для всех остальных маршрутов — нужна авторизация

  // если ещё не загружали профиль — пробуем получить его с бэка
  if (auth.user === null) {
    await auth.fetchProfile()
  }

  // если всё ещё не авторизован — отправляем на логин
  if (!auth.isAuthenticated) {
    return next({
      name: "LoginView",
      query: { next: to.fullPath }, // можно потом использовать для редиректа обратно
    })
  }

  // всё ок — продолжаем
  next()
})

export default router