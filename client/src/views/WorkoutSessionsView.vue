<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import Cookies from "js-cookie"
import _ from "lodash"

const workoutSessions = ref([])
const users = ref([])

const loading = ref(false)
const stats = ref(null)
const profile = ref(null)

const workoutSessionsToAdd = ref({ client: null, trainer: null, session_date: "" })
const workoutSessionsToEdit = ref({})

const usersById = computed(() => _.keyBy(users.value, x => x.id))

const clientsForForm = computed(() =>
  users.value.filter(u => u.role === "client")
)
const trainersForForm = computed(() =>
  users.value.filter(u => u.role === "trainer")
)

const clientNameById = id => usersById.value[id]?.name || ""
const trainerNameById = id => usersById.value[id]?.name || ""

const isAdmin = computed(() => !!profile.value?.is_superuser)

const formattedAvgPerClient = computed(() => {
  if (!stats.value || stats.value.avg_per_client == null) return "0.0"
  return Number(stats.value.avg_per_client).toFixed(1)
})


async function fetchProfile() {
  try {
    const r = await axios.get("/api/userprofile/info/")
    profile.value = r.data
  } catch (e) {
    profile.value = null
  }
}

async function fetchUsers() {
  const r = await axios.get("/api/users/")
  users.value = r.data
}

async function fetchWorkoutSessionsAndStats() {
  const [listRes, statsRes] = await Promise.all([
    axios.get("/api/workoutsession/"),
    axios.get("/api/workoutsession/stats/"),
  ])
  workoutSessions.value = listRes.data
  stats.value = statsRes.data
}


async function onWorkoutSessionsAdd() {
  await axios.post("/api/workoutsession/", { ...workoutSessionsToAdd.value })

  workoutSessionsToAdd.value = { client: null, trainer: null, session_date: "" }
  await fetchWorkoutSessionsAndStats()
}

async function onRemoveClick(workoutsession) {
  if (!isAdmin.value) return

  await axios.delete(`/api/workoutsession/${workoutsession.id}/`)
  await fetchWorkoutSessionsAndStats()
}

function onWorkoutSessionsEditClick(workoutsession) {
  if (!isAdmin.value) return

  workoutSessionsToEdit.value = { ...workoutsession }
  if (workoutSessionsToEdit.value.session_date) {
    const d = new Date(workoutSessionsToEdit.value.session_date)
    const pad = n => String(n).padStart(2, "0")
    const local = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(
      d.getDate()
    )}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    workoutSessionsToEdit.value.session_date = local
  }
}

async function onUpdateWorkoutSessions() {
  if (!isAdmin.value) return

  await axios.patch(`/api/workoutsession/${workoutSessionsToEdit.value.id}/`, {
    client: workoutSessionsToEdit.value.client,
    trainer: workoutSessionsToEdit.value.trainer,
    session_date: workoutSessionsToEdit.value.session_date,
  })
  await fetchWorkoutSessionsAndStats()
}

onBeforeMount(async () => {
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")
  loading.value = true
  await fetchProfile()
  await Promise.all([
    fetchUsers(),                
    fetchWorkoutSessionsAndStats()
  ])
  loading.value = false
})
</script>

<template>
  <div class="modal fade" id="editWorkoutSessionsModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Редактировать тренировку</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
        </div>

        <div class="modal-body">
          <div class="row g-2">
            <div class="col-md-4">
              <div class="form-floating">
                <select class="form-select" v-model="workoutSessionsToEdit.client">
                  <option
                    :value="client.id"
                    v-for="client in clientsForForm"
                    :key="`e-c-${client.id}`"
                  >
                    {{ client.name }}
                  </option>
                </select>
                <label>Клиент</label>
              </div>
            </div>

            <div class="col-md-4">
              <div class="form-floating">
                <select class="form-select" v-model="workoutSessionsToEdit.trainer">
                  <option
                    :value="trainer.id"
                    v-for="trainer in trainersForForm"
                    :key="`e-t-${trainer.id}`"
                  >
                    {{ trainer.name }}
                  </option>
                </select>
                <label>Тренер</label>
              </div>
            </div>

            <div class="col-md-4">
              <div class="form-floating">
                <input
                  type="datetime-local"
                  class="form-control"
                  v-model="workoutSessionsToEdit.session_date"
                  required
                />
                <label>Дата</label>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
          <button
            class="btn btn-primary"
            data-bs-dismiss="modal"
            @click="onUpdateWorkoutSessions"
          >
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid">
    <div class="p-2">
      <div class="row g-2">
        <div class="col">
          <div class="form-floating">
            <select class="form-select" v-model="workoutSessionsToAdd.client" required>
              <option
                :value="client.id"
                v-for="client in clientsForForm"
                :key="`a-c-${client.id}`"
              >
                {{ client.name }}
              </option>
            </select>
            <label>Клиент</label>
          </div>
        </div>

        <div class="col-auto">
          <div class="form-floating">
            <select class="form-select" v-model="workoutSessionsToAdd.trainer" required>
              <option
                :value="trainer.id"
                v-for="trainer in trainersForForm"
                :key="`a-t-${trainer.id}`"
              >
                {{ trainer.name }}
              </option>
            </select>
            <label>Тренер</label>
          </div>
        </div>

        <div class="col">
          <div class="form-floating">
            <input
              type="datetime-local"
              class="form-control"
              v-model="workoutSessionsToAdd.session_date"
              required
            />
            <label>Дата</label>
          </div>
        </div>

        <div class="col-auto">
          <button class="btn btn-primary" @click="onWorkoutSessionsAdd">
            Добавить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid" v-if="stats">
    <div class="alert alert-info py-2 mb-2">
      <strong>Статистика тренировок:</strong><br />
      <span class="ms-3">
        всего: {{ stats.total }}<br />
      </span>
      <span class="ms-3">
        за последние 7 дней: {{ stats.last_7_days }}<br />
      </span>
      <span class="ms-3">
        предстоящие: {{ stats.upcoming }}<br />
      </span>
      <span class="ms-3">
        среднее на клиента: {{ formattedAvgPerClient }}<br />
      </span>
      <template v-if="stats.top_trainer_name">
        <span class="ms-3">
          самый загруженный тренер: {{ stats.top_trainer_name }}
          ({{ stats.top_trainer_sessions }} тренировок)<br />
        </span>
      </template>
      <template v-if="stats.top_client_name">
        <span class="ms-3">
          самый активный клиент: {{ stats.top_client_name }}
          ({{ stats.top_client_sessions }} тренировок)
        </span>
      </template>
    </div>
  </div>

  <div v-if="loading" class="p-3 text-center">Загрузка…</div>
  <div v-else>
    <div
      v-for="item in workoutSessions"
      :key="item.id"
      class="workoutSessions-item"
    >
      <div>{{ clientNameById(item.client) }}</div>
      <div>{{ trainerNameById(item.trainer) }}</div>
      <div>{{ new Date(item.session_date).toLocaleString() }}</div>

      <button
        v-if="isAdmin"
        class="btn btn-success"
        @click="onWorkoutSessionsEditClick(item)"
        data-bs-toggle="modal"
        data-bs-target="#editWorkoutSessionsModal"
      >
        <i class="bi bi-pen-fill" />
      </button>
      <button
        v-if="isAdmin"
        class="btn btn-danger"
        @click="onRemoveClick(item)"
      >
        <i class="bi bi-x" />
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.workoutSessions-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 1fr auto auto auto;
  gap: 16px;
}
</style>