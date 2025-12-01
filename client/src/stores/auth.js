import { defineStore } from "pinia"
import { ref, computed } from "vue"
import axios from "axios"
import Cookies from "js-cookie"

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null)        // тут будет ответ /api/userprofile/info/
  const loading = ref(false)
  const error = ref(null)
  const otpGood = ref(false)

  // CSRF один раз
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken") || ""

  const isAuthenticated = computed(() => !!user.value?.is_authenticated)

  const isAdmin = computed(() => {
    const u = user.value
    if (!u) return false
    return Boolean(u.is_superuser || u.is_admin || u.role === "admin")
  })

  const isClient = computed(() => user.value?.role === "client")
  const isTrainer = computed(() => user.value?.role === "trainer")

  async function fetchProfile() {
    loading.value = true
    error.value = null
    try {
      const r = await axios.get("/api/userprofile/info/")
      user.value = r.data
    } catch (e) {
      console.error("fetchProfile error", e)
      user.value = null
      error.value = "Не удалось получить профиль"
    } finally {
      loading.value = false
    }
  }

  async function login(username, password) {
    loading.value = true
    error.value = null
    try {
      await axios.post("/api/userprofile/login/", { username, password })
      await fetchProfile()
      return true
    } catch (e) {
      console.error("login error", e)
      error.value = "Неверный логин или пароль"
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    error.value = null
    try {
      await axios.post("/api/userprofile/logout/")
    } catch (e) {
      console.error("logout error", e)
    } finally {
      user.value = null
      otpGood.value = false
      loading.value = false
    }
  }

  async function fetchOtpStatus() {
    try {
      const r = await axios.get("/api/userprofile/otp-status/")
      otpGood.value = !!r.data.otp_good
    } catch (e) {
      console.error("otp-status error", e)
      otpGood.value = false
    }
  }

  async function otpLogin(code) {
    try {
      await axios.post("/api/userprofile/otp-login/", { key: code })
      await fetchOtpStatus()
    } catch (e) {
      console.error("otp-login error", e)
    }
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    isClient,
    isTrainer,
    otpGood,
    fetchProfile,
    login,
    logout,
    fetchOtpStatus,
    otpLogin,
  }
})