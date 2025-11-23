<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from 'js-cookie'

const clients = ref([]);
const loading = ref(false)
const clientToAdd = ref([])
const clientToEdit = ref({})
const clientsPictureRef = ref()
const clientsAddImageUrl = ref()
const clientsEditPictureRef = ref()
const clientsEditImageUrl = ref()
const imageModalUrl = ref('')

async function fetchClients() {
  loading.value = true
  const r = await axios.get("/api/clients/")
  console.log(r.data)
  clients.value = r.data
  loading.value = false
}
async function onClientAdd() {
  const formData = new FormData()
  formData.append('picture', clientsPictureRef.value.files[0])

  formData.set('name', clientToAdd.value.name)
  formData.set('phone', clientToAdd.value.phone)
  await axios.post("/api/clients/", formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  await fetchClients()
}

async function onRemoveClick(client) {
  await axios.delete(`/api/clients/${client.id}/`);
  await fetchClients();
}

async function onClientEditClick(client) {
  clientToEdit.value = { ...client }
  clientsEditImageUrl.value = client.picture
}

async function onUpdateClient() {
  const formData = new FormData()

  formData.append('picture', clientsEditPictureRef.value.files[0])
  formData.append('name', clientToEdit.value.name)
  formData.append('phone', clientToEdit.value.phone)

  await axios.put(`/api/clients/${clientToEdit.value.id}/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  await fetchTrainers()
}
async function clientsAddPictureChange() {
  clientsAddImageUrl.value = URL.createObjectURL(clientsPictureRef.value.files[0])
}

function clientsEditPictureChange() {
  clientsEditImageUrl.value = URL.createObjectURL(clientsEditPictureRef.value.files[0])
}

function openImageModal(imageUrl) {
  imageModalUrl.value = imageUrl
}

onBeforeMount(async () => {
  await fetchClients()
  axios.defaults.headers.common['X-CSRFToken'] = Cookies.get("csrftoken");
})
</script>

<template>
  <div class="modal fade" id="imageModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Просмотр изображения</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body text-center">
          <img :src="imageModalUrl" class="img-fluid" style="max-height: 70vh;" alt="">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            Закрыть
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="modal fade" id="editClientModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="exampleModalLabel">
            редактировать
          </h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <div class="col">
              <div class="form-floating">
                <input type="text" class="form-control" v-model="clientToEdit.name">
                <label for="floatingInput">ФИО</label>
              </div>
            </div>
            <div class="col-auto">
              <div class="form-floating">
                <input type="text" class="form-control" v-model="clientToEdit.phone">
                <label for="floatingInput">Телефон</label>
              </div>
            </div>
            <div class="col-auto">
              <input type="file" class="form-control" ref="clientsEditPictureRef" @change="clientsEditPictureChange">
            </div>
            <div class="col-auto">
              <img :src="clientsEditImageUrl" style="max-width: 60px;" alt="">
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            Закрыть
          </button>
          <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateClient">
            Сохранить
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container-fluid">
    <div class="p-2">
      <div class="row">
        <div class="col">
          <div class="form-floating">
            <input type="text" class="form-control" v-model="clientToAdd.name" required>
            <label for="floatingInput">ФИО</label>
          </div>
        </div>
        <div class="col-auto">
          <div class="form-floating">
            <input type="text" class="form-control" v-model="clientToAdd.phone" required>
            <label for="floatingInput">Телефон</label>
          </div>
        </div>
        <div class="col-auto">
          <input type="file" class="form-control" ref="clientsPictureRef" @change="clientsAddPictureChange">
        </div>
        <div class="col-auto">
          <img :src="clientsAddImageUrl" style="max-width: 60px;" alt="">
        </div>
        <div class="col-auto">
          <button class="btn btn-primary" @click="onClientAdd">Добавить</button>
        </div>
      </div>
    </div>


    <div>
      <div v-for="item in clients" class="client-item">
        <div>{{ item.name }} </div>
        <div>{{ item.phone }}</div>
        <div v-show="item.picture"><img :src="item.picture" data-bs-toggle="modal" data-bs-target="#imageModal"
            @click="openImageModal(item.picture)" style="max-width: 60px; cursor: pointer;" alt=""></div>
        <button class="btn btn-success" @click="onClientEditClick(item)" data-bs-toggle="modal"
          data-bs-target="#editClientModal">
          <i class="bi bi-pen-fill"></i>
        </button>
        <button class="btn btn-danger" @click="onRemoveClick(item)">
          <i class="bi bi-x"></i>
        </button>
      </div>
    </div>
  </div>
</template>


<style lang="scss" scoped>
.client-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr auto auto auto auto;
  gap: 16px;
}
</style>
