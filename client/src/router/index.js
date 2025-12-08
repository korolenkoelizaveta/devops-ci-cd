import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

import UsersView from "@/views/UsersView.vue"
import MembershipsView from "@/views/MembershipsView.vue"
import MembershipTypesView from "@/views/MembershipTypesView.vue"
import WorkoutSessionsView from "@/views/WorkoutSessionsView.vue"
import LoginView from "@/views/LoginView.vue"
import SecondFactorView from "@/views/SecondFactorView.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [

    {
      path: "/login",
      name: "LoginView",
      component: LoginView,
    },
    {
      path: "/second-factor",
      name: "SecondFactorView",
      component: SecondFactorView
    },
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

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()

  if (to.name === "LoginView") {
    if (auth.isAuthenticated && auth.otpGood) {
      return next({ name: "UsersView" })
    }
    return next()
  }

  if (auth.user === null) {
    await auth.fetchProfile()
  }

  if (!auth.isAuthenticated) {
    return next({
      name: "LoginView",
      query: { next: to.fullPath }
    })
  }

  if (auth.otpGood === null) {
    await auth.fetchOtpStatus()
  }

  if (!auth.otpGood && to.name !== "SecondFactorView") {
    return next({ name: "SecondFactorView" })
  }

  if (auth.otpGood && to.name === "SecondFactorView") {
    return next({ name: "UsersView" })
  }

  next()
})


export default router