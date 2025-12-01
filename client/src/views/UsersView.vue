<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import Cookies from "js-cookie"
import { useAuthStore } from "@/stores/auth"

const auth = useAuthStore()

const users = ref([])
const loading = ref(false)
const stats = ref(null)

// фильтры
const selectedRoleFilter = ref("")      // клиент / тренер
const nameFilter = ref("")              // фильтр по ФИО
const trainerSpecFilter = ref("")       // фильтр по специализации тренера (select)

// форма добавления / редактирования
const userToAdd = ref({ name: "", role: "client", phone: "", specialization: "" })
const userPictureRef = ref()
const userAddImageUrl = ref("")

const userToEdit = ref({})
const editPictureRef = ref()
const editImageUrl = ref("")

const imageModalUrl = ref("")

// кто залогинен (берём из auth.user)
const isAdminProfile = computed(() => {
  const u = auth.user
  if (!u) return false
  return Boolean(u.is_superuser ||  u.is_admin ||  u.role === "admin")
})
const isTrainerProfile = computed(() => auth.user?.role === "trainer")

// может ли управлять пользователями (создание/редакт/удаление)
const canManageUsers = computed(() => isAdminProfile.value)

// доступные специализации тренеров (для выпадающего списка)
const trainerSpecs = computed(() => {
  const set = new Set()
  for (const u of users.value) {
    if (u.role === "trainer" && u.specialization) {
      set.add(u.specialization)
    }
  }
  return Array.from(set)
})

// -------- фильтрация по столбцам --------
const filteredUsers = computed(() => {
  let res = users.value.slice()

  // фильтр по роли (столбец "роль")
  if (selectedRoleFilter.value) {
    res = res.filter(u => u.role === selectedRoleFilter.value)
  }

  // фильтр по ФИО
  if (nameFilter.value.trim()) {
    const needle = nameFilter.value.toLowerCase()
    res = res.filter(u => (u.name || "").toLowerCase().includes(needle))
  }

  // фильтр по специализации тренера (только у тренеров), через выпадающий список
  if (trainerSpecFilter.value) {
    res = res.filter(u => {
      if (u.role !== "trainer") return true      // клиенты не режутся этим фильтром
      return u.specialization === trainerSpecFilter.value
    })
  }

  return res
})

// -------- статистика --------
const statsMessage = computed(() => {
  if (!stats.value) return ""
  const s = stats.value

  // для клиента: нет клиентов, есть тренеры → «доступных тренеров»
  if (s.clients === 0 && s.trainers > 0) {
    return `Доступных тренеров: ${s.trainers}`
  }

  // для тренера: есть клиенты, нет тренеров → «моих клиентов»
  if (s.trainers === 0 && s.clients > 0) {
    return `Моих клиентов: ${s.clients}`
  }

  // для админа — общая статистика
  return `Всего: ${s.count}, клиентов: ${s.clients}, тренеров: ${s.trainers}`
})

// -------- запросы --------
async function fetchUsers() {
  loading.value = true

  // НИКАКИХ ?role= — бэкенд сам режет список по роли
  const [usersRes, statsRes] = await Promise.all([
    axios.get("/api/users/"),
    axios.get("/api/users/stats/"),
  ])

  users.value = usersRes.data
  stats.value = statsRes.data
  loading.value = false
}

async function onUserAdd() {
  if (!canManageUsers.value) return

  const formData = new FormData()

  if (userPictureRef.value?.files?.[0]) {
    formData.append("picture", userPictureRef.value.files[0])
  }

  formData.append("name", userToAdd.value.name || "")
  formData.append("role", userToAdd.value.role)

  if (userToAdd.value.role === "client") {
    formData.append("phone", userToAdd.value.phone || "")
  } else {
    formData.append("specialization", userToAdd.value.specialization || "")
  }

  await axios.post("/api/users/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })

  await fetchUsers()

  userToAdd.value = { name: "", role: "client", phone: "", specialization: "" }
  if (userPictureRef.value) {
    userPictureRef.value.value = ""
  }
  userAddImageUrl.value = ""
}

async function onRemoveClick(user) {
  if (!canManageUsers.value) return
  await axios.delete(`/api/users/${user.id}/`)
  await fetchUsers()
}

async function onUserEditClick(user) {
  if (!canManageUsers.value) return
  userToEdit.value = { ...user }
  editImageUrl.value = user.picture
}

async function onUpdateUser() {
  if (!canManageUsers.value) return

  const formData = new FormData()

  if (editPictureRef.value?.files?.[0]) {
    formData.append("picture", editPictureRef.value.files[0])
  }

  formData.append("name", userToEdit.value.name || "")

  if (userToEdit.value.role === "client") {
    formData.append("phone", userToEdit.value.phone || "")
  } else {
    formData.append("specialization", userToEdit.value.specialization || "")
  }

  await axios.patch(`/api/users/${userToEdit.value.id}/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })

  await fetchUsers()
}

// -------- картинки --------
function onAddPictureChange() {
  if (userPictureRef.value?.files?.[0]) {
    userAddImageUrl.value = URL.createObjectURL(userPictureRef.value.files[0])
  }
}

function onEditPictureChange() {
  if (editPictureRef.value?.files?.[0]) {
    editImageUrl.value = URL.createObjectURL(editPictureRef.value.files[0])
  }
}

function openImageModal(imageUrl) {
  imageModalUrl.value = imageUrl
}

onBeforeMount(async () => {
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken") || ""

  // если профиль ещё не загружен (например, после F5), подтянем его
  if (auth.user === null) {
    await auth.fetchProfile()
  }

  await fetchUsers()
})

async function onExportXlsx() {
  try {
    const response = await axios.get("/api/users/export-excel/", {
      responseType: "blob",
    })

    const contentType = response.headers["content-type"] || ""

    // Если вдруг бэк вернул JSON (ошибка), а не файл
    if (contentType.includes("application/json")) {
      const text = await response.data.text()
      try {
        const json = JSON.parse(text)
        alert(json.detail || json.error || "Ошибка при экспорте")
      } catch {
        alert("Ошибка при экспорте файла")
      }
      return
    }

    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "users.xlsx"
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error(err)
    alert("Не удалось скачать файл (см. консоль браузера/сервер)")
  }
}
</script>

<template>
  <!-- модалка просмотра картинки -->
  <div class="modal fade" id="imageModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Просмотр изображения</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body text-center">
          <img :src="imageModalUrl" class="img-fluid" style="max-height:70vh" alt="" />
        </div>
      </div>
    </div>
  </div>

  <!-- модалка редактирования пользователя -->
  <div class="modal fade" id="editUserModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Редактировать</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <div class="form-floating mb-2">
            <input type="text" class="form-control" v-model="userToEdit.name" />
            <label>ФИО</label>
          </div>

          <div v-if="userToEdit.role === 'client'" class="form-floating mb-2">
            <input type="text" class="form-control" v-model="userToEdit.phone" />
            <label>Телефон</label>
          </div>

          <div v-else class="form-floating mb-2">
            <input type="text" class="form-control" v-model="userToEdit.specialization" />
            <label>Специализация</label>
          </div>

          <input
            type="file"
            class="form-control mb-2"
            ref="editPictureRef"
            @change="onEditPictureChange"
          />
          <img :src="editImageUrl" v-if="editImageUrl" style="max-width:60px" alt="" />
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
          <button class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateUser">
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid p-3">
    <!-- форма добавления только для админа -->
    <div class="row g-2 align-items-center mb-3" v-if="canManageUsers">
      <div class="col">
        <div class="form-floating">
          <input type="text" class="form-control" v-model="userToAdd.name" required />
          <label>ФИО</label>
        </div>
      </div>

      <div class="col-auto">
        <div class="form-floating">
          <select class="form-select" v-model="userToAdd.role">
            <option value="client">Клиент</option>
            <option value="trainer">Тренер</option>
          </select>
          <label>Роль</label>
        </div>
      </div>

      <div class="col-auto" v-if="userToAdd.role === 'client'">
        <div class="form-floating">
          <input type="text" class="form-control" v-model="userToAdd.phone" required />
          <label>Телефон</label>
        </div>
      </div>

      <div class="col-auto" v-if="userToAdd.role === 'trainer'">
        <div class="form-floating">
          <input
            type="text"
            class="form-control"
            v-model="userToAdd.specialization"
            required
          />
          <label>Специализация</label>
        </div>
      </div>

      <div class="col-auto">
        <input
          type="file"
          class="form-control"
          ref="userPictureRef"
          @change="onAddPictureChange"
        />
      </div>
      <div class="col-auto">
        <img :src="userAddImageUrl" v-if="userAddImageUrl" style="max-width:60px" alt="" />
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="onUserAdd">Добавить</button>
      </div>
    </div>

    <!-- строка фильтров по столбцам -->
    <div class="row mb-3 g-2">
  <!-- фильтр по роли -->
  <div class="col-auto">
    <select class="form-select" v-model="selectedRoleFilter">
      <option value="">Все пользователи</option>
      <option value="client">Клиенты</option>
      <option value="trainer">Тренеры</option>
    </select>
  </div>

  <!-- фильтр по ФИО -->
  <div class="col-auto">
    <input
      type="text"
      class="form-control"
      v-model="nameFilter"
      placeholder="Фильтр по ФИО"
    />
  </div>

  <!-- фильтр по специализации тренера -->
  <div class="col-auto" v-if="!isTrainerProfile">
    <select class="form-select" v-model="trainerSpecFilter">
      <option value="">Все специализации</option>
      <option v-for="spec in trainerSpecs" :key="spec" :value="spec">
        {{ spec }}
      </option>
    </select>
  </div>

  <!-- КНОПКА ЭКСПОРТА -->
  <div class="col-auto ms-auto" v-if="isAdminProfile">
    <button class="btn btn-outline-secondary" @click="onExportXlsx">
      <i class="bi bi-file-earmark-excel me-1"></i>
      Скачать в Excel
    </button>
  </div>
</div>

    

    <!-- статистика -->
    <div class="row mb-3" v-if="stats">
      <div class="col">
        <div class="alert alert-info py-2 mb-0">
          <strong>Статистика пользователей:</strong>
          <span class="ms-2">{{ statsMessage }}</span>
        </div>
      </div>
    </div>

    <!-- список пользователей -->
    <div v-if="loading" class="text-center p-3">Загрузка...</div>
    <div v-else>
      <div v-for="user in filteredUsers" :key="user.id" class="user-item">
        <div>{{ user.name }}</div>
        <div v-show="user.picture">
          <img
            :src="user.picture"
            data-bs-toggle="modal"
            data-bs-target="#imageModal"
            @click="openImageModal(user.picture)"
            style="max-width:60px; cursor:pointer;"
            alt=""
          />
        </div>
        <div>
          <span v-if="user.role === 'client'">{{ user.phone || '—' }}</span>
          <span v-else>{{ user.specialization || "—" }}</span>
        </div>
        <div>
          <span class="badge bg-secondary">
            {{ user.role === "client" ? "Клиент" : "Тренер" }}
          </span>
        </div>

        <button
          v-if="canManageUsers"
          class="btn btn-success"
          @click="onUserEditClick(user)"
          data-bs-toggle="modal"
          data-bs-target="#editUserModal"
        >
          <i class="bi bi-pen-fill"></i>
        </button>
        <button
          v-if="canManageUsers"
          class="btn btn-danger"
          @click="onRemoveClick(user)"
        >
          <i class="bi bi-x"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.user-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr auto auto auto auto auto;
  gap: 12px;
}
</style>