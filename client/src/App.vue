<script setup>
import { computed, onBeforeMount } from "vue"
import { useRoute, useRouter, RouterView, RouterLink } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// шапку и меню не показываем на странице логина
const showLayout = computed(() => route.name !== "LoginView")

// подпись в шапке: имя + роль
const userLabel = computed(() => {
  const u = auth.user
  if (!u || !auth.isAuthenticated) return ""

  let roleText = ""
  if (u.is_admin || u.is_superuser) roleText = "админ"
  else if (u.role === "trainer") roleText = "тренер"
  else if (u.role === "client") roleText = "клиент"

  return roleText ? `${u.username} (${roleText})` : u.username
})

async function onLogout() {
  await auth.logout()
  router.push({ name: "LoginView" })
}

// при первом заходе пробуем подтянуть профиль,
// если вдруг стор ещё пустой (на случай обновления страницы)
onBeforeMount(async () => {
  if (auth.user === null) {
    await auth.fetchProfile()
  }
})
</script>

<template>
  <!-- страница логина — без шапки, просто рендерим RouterView -->
  <RouterView v-if="!showLayout" />

  <!-- все остальные страницы -->
  <div v-else>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <RouterLink class="navbar-brand" to="/users">
          Gym
        </RouterLink>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mainNavbar"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="mainNavbar">
          <!-- ЛЕВАЯ ЧАСТЬ: разделы -->
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink
                to="/users"
                class="nav-link"
                :class="{ active: route.name === 'UsersView' }"
              >
                Пользователи
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/memberships"
                class="nav-link"
                :class="{ active: route.name === 'MembershipsView' }"
              >
                Абонементы
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/membershiptypes"
                class="nav-link"
                :class="{ active: route.name === 'MembershipTypesView' }"
              >
                Типы абонементов
              </RouterLink>
            </li>
            <li class="nav-item">
              <RouterLink
                to="/workoutsessions"
                class="nav-link"
                :class="{ active: route.name === 'WorkoutSessionsView' }"
              >
                Тренировки
              </RouterLink>
            </li>
          </ul>

          <!-- ПРАВАЯ ЧАСТЬ: текущий пользователь + выход -->
          <div class="d-flex align-items-center">
            <span
              v-if="auth.isAuthenticated && userLabel"
              class="text-light me-3"
            >
              {{ userLabel }}
            </span>

            <button
              v-if="auth.isAuthenticated"
              class="btn btn-outline-light btn-sm"
              @click="onLogout"
            >
              Выйти
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="container-fluid py-3">
      <RouterView />
    </main>
  </div>
</template>