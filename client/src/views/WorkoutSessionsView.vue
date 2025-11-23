<script setup>
import axios from "axios"
import { ref, onBeforeMount, computed } from "vue"
import Cookies from "js-cookie"
import _ from "lodash"

const workoutSessions = ref([])
const clients = ref([])   // /api/users/?role=client
const trainers = ref([])  // /api/users/?role=trainer
const loading = ref(false)

const workoutSessionsToAdd = ref({ client: null, trainer: null, session_date: "" })
const workoutSessionsToEdit = ref({})

const clientsById = computed(() => _.keyBy(clients.value, x => x.id))
const trainersById = computed(() => _.keyBy(trainers.value, x => x.id))

async function fetchWorkoutSessions() {
  loading.value = true
  const r = await axios.get("/api/workoutsession/")
  workoutSessions.value = r.data
  loading.value = false
}

async function fetchClients() {
  const r = await axios.get("/api/users/?role=client")
  clients.value = r.data
}
async function fetchTrainers() {
  const r = await axios.get("/api/users/?role=trainer")
  trainers.value = r.data
}

async function onWorkoutSessionsAdd() {
  await axios.post("/api/workoutsession/", { ...workoutSessionsToAdd.value })
  workoutSessionsToAdd.value = { client: null, trainer: null, session_date: "" }
  await fetchWorkoutSessions()
}

async function onRemoveClick(workoutsession) {
  await axios.delete(`/api/workoutsession/${workoutsession.id}/`)
  await fetchWorkoutSessions()
}

function onWorkoutSessionsEditClick(workoutsession) {
  workoutSessionsToEdit.value = { ...workoutsession }
  if (workoutSessionsToEdit.value.session_date) {
    const d = new Date(workoutSessionsToEdit.value.session_date)
    const pad = n => String(n).padStart(2, "0")
    const local = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
    workoutSessionsToEdit.value.session_date = local
  }
}

async function onUpdateWorkoutSessions() {
  await axios.patch(`/api/workoutsession/${workoutSessionsToEdit.value.id}/`, {
    client: workoutSessionsToEdit.value.client,
    trainer: workoutSessionsToEdit.value.trainer,
    session_date: workoutSessionsToEdit.value.session_date, 
  })
  await fetchWorkoutSessions()
}

onBeforeMount(async () => {
  axios.defaults.headers.common["X-CSRFToken"] = Cookies.get("csrftoken")
  await Promise.all([fetchWorkoutSessions(), fetchClients(), fetchTrainers()])
})
</script>

<template>
  <div class="modal fade" id="editWorkoutSessionsModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Редактировать тренировку</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>

        <div class="modal-body">
          <div class="row g-2">
            <div class="col-md-4">
              <div class="form-floating">
                <select class="form-select" v-model="workoutSessionsToEdit.client">
                  <option :value="client.id" v-for="client in clients" :key="`e-c-${client.id}`">
                    {{ client.name }}
                  </option>
                </select>
                <label>Клиент</label>
              </div>
            </div>

            <div class="col-md-4">
              <div class="form-floating">
                <select class="form-select" v-model="workoutSessionsToEdit.trainer">
                  <option :value="trainer.id" v-for="trainer in trainers" :key="`e-t-${trainer.id}`">
                    {{ trainer.name }}
                  </option>
                </select>
                <label>Тренер</label>
              </div>
            </div>

            <div class="col-md-4">
              <div class="form-floating">
                <input type="datetime-local" class="form-control" v-model="workoutSessionsToEdit.session_date" required>
                <label>Дата</label>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
          <button class="btn btn-primary" data-bs-dismiss="modal" @click="onUpdateWorkoutSessions">Сохранить</button>
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
              <option :value="client.id" v-for="client in clients" :key="`a-c-${client.id}`">{{ client.name }}</option>
            </select>
            <label>Клиент</label>
          </div>
        </div>

        <div class="col-auto">
          <div class="form-floating">
            <select class="form-select" v-model="workoutSessionsToAdd.trainer" required>
              <option :value="trainer.id" v-for="trainer in trainers" :key="`a-t-${trainer.id}`">{{ trainer.name }}</option>
            </select>
            <label>Тренер</label>
          </div>
        </div>

        <div class="col">
          <div class="form-floating">
            <input type="datetime-local" class="form-control" v-model="workoutSessionsToAdd.session_date" required>
            <label>Дата</label>
          </div>
        </div>

        <div class="col-auto">
          <button class="btn btn-primary" @click="onWorkoutSessionsAdd">Добавить</button>
        </div>
      </div>
    </div>
  </div>

  <div v-if="loading" class="p-3 text-center">Загрузка…</div>
  <div v-else>
    <div v-for="item in workoutSessions" :key="item.id" class="workoutSessions-item">
      <div>{{ clientsById[item.client]?.name }}</div>
      <div>{{ trainersById[item.trainer]?.name }}</div>
      <div>{{ new Date(item.session_date).toLocaleString() }}</div>
      <button class="btn btn-success" @click="onWorkoutSessionsEditClick(item)" data-bs-toggle="modal" data-bs-target="#editWorkoutSessionsModal">
        <i class="bi bi-pen-fill"></i>
      </button>
      <button class="btn btn-danger" @click="onRemoveClick(item)">
        <i class="bi bi-x"></i>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.workoutSessions-item {
  padding: .5rem;
  margin: .5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr 1fr auto auto auto;
  gap: 16px;
}
</style>
