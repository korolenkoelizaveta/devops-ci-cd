<script setup>
import { ref, watch } from "vue"
import axios from "axios"
import QRCode from "qrcode"
import { useAuthStore } from "@/stores/auth"
import { useRouter, useRoute } from "vue-router"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const totpUrl = ref("")
const qrcodeUrl = ref("")
const code = ref("")
const error = ref("")

// когда получили новый otpauth://..., генерим картинку QR
watch(totpUrl, async (value) => {
  if (!value) {
    qrcodeUrl.value = ""
    return
  }
  qrcodeUrl.value = await QRCode.toDataURL(value)
})

async function onGetKey() {
  error.value = ""
  try {
    const r = await axios.get("/api/userprofile/otp-get-key/")
    totpUrl.value = r.data.url
  } catch (e) {
    console.error("otp-get-key error", e)
    error.value = "Не удалось получить ключ для приложения"
  }
}

async function onSubmit() {
  error.value = ""
  try {
    await auth.otpLogin(code.value)
    await auth.fetchOtpStatus()

    if (!auth.otpGood) {
      error.value = "Неверный код"
      return
    }

    // редирект туда, куда хотели изначально (next), или на /users
    const next = route.query.next || "/users"
    router.push(next)
  } catch (e) {
    console.error("otp-login error", e)
    error.value = "Не удалось проверить код"
  }
}
</script>

<template>
  <div class="container py-4" style="max-width: 600px">
    <h2 class="mb-3">Двухфакторная авторизация</h2>
    <ol class="mb-3">
      <li>Нажмите «Получить ключ», отсканируйте QR-код в приложении (Google Authenticator и т.п.).</li>
      <li>Введите одноразовый код из приложения.</li>
    </ol>

    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div class="card mb-3">
      <div class="card-body">
        <button class="btn btn-outline-primary mb-3" @click="onGetKey">
          Получить ключ для приложения
        </button>

        <div v-if="qrcodeUrl" class="text-center">
          <img :src="qrcodeUrl" alt="QR code" class="img-fluid" style="max-height: 260px" />
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-body">
        <label class="form-label">Код из приложения</label>
        <input
          type="text"
          class="form-control mb-3"
          v-model="code"
          placeholder="123456"
        />
        <button class="btn btn-primary w-100" @click="onSubmit">
          Подтвердить
        </button>
      </div>
    </div>
  </div>
</template>
