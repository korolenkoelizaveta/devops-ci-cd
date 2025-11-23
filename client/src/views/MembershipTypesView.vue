<script setup>
import axios from "axios"
import { ref, onBeforeMount } from "vue"
import Cookies from 'js-cookie'

const membershipTypes = ref([]);
const loading = ref(false)
const membershipTypeToAdd = ref([])
const membershipTypeToEdit = ref({});

async function fetchMembershipTypes() {
  loading.value = true
  const r = await axios.get("/api/membershiptype/")
  console.log(r.data)
  membershipTypes.value = r.data
  loading.value = false
}
async function onMembershipTypeAdd() {
  await axios.post("/api/membershiptype/", {
    ...membershipTypeToAdd.value
  })
  await fetchMembershipTypes()
}

async function onRemoveClick(membershiptype) {
  await axios.delete(`/api/membershiptype/${membershiptype.id}/`);
  await fetchMembershipTypes();
}

async function onMembershipTypeEditClick(membershiptype) {
  membershipTypeToEdit.value = {...membershiptype}
}

async function onUpdateMembershipType() {
  await axios.put(`/api/membershiptype/${membershipTypeToEdit.value.id}/`, {
    ...membershipTypeToEdit.value,
  })
  await fetchMembershipTypes();
}

onBeforeMount(async () => {
  await fetchMembershipTypes()
  axios.defaults.headers.common['X-CSRFToken'] = Cookies.get("csrftoken");
})
</script>

<template>
  <div class="modal fade" id="editMembershipTypeModal" tabindex="-1">
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
          <input type="text" class="form-control" v-model="membershipTypeToEdit.type">
          <label for="floatingInput">Тип абонемента</label>
        </div>
      </div>
      <div class="col-auto">
        <div class="form-floating">
          <input type="text" class="form-control" v-model="membershipTypeToEdit.duration">
          <label for="floatingInput">Описание</label>
        </div>
      </div>
    </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
            Закрыть
          </button>
          <button data-bs-dismiss="modal" type="button" class="btn btn-primary" @click="onUpdateMembershipType">
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
          <input type="text" class="form-control" v-model="membershipTypeToAdd.type" required>
          <label for="floatingInput">Тип абонемента</label>
        </div>
      </div>
      <div class="col-auto">
        <div class="form-floating">
          <input type="text" class="form-control" v-model="membershipTypeToAdd.duration" required>
          <label for="floatingInput">Описание</label>
        </div>
      </div>
      <div class="col-auto">
        <button class="btn btn-primary" @click="onMembershipTypeAdd">Добавить</button>
      </div>
    </div>
</div>


    <div>
      <div v-for="item in membershipTypes" class="membershipType-item">
        <div>{{ item.type }} </div>
        <div>{{ item.description }}</div>
        <button class="btn btn-success" @click="onMembershipTypeEditClick(item)" data-bs-toggle="modal"
          data-bs-target="#editMembershipTypeModal">
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
.membershipType-item {
  padding: 0.5rem;
  margin: 0.5rem;
  border: 1px solid silver;
  border-radius: 8px;
  display: grid;
  align-items: center;
  grid-template-columns: 1fr auto auto auto;
  gap: 16px;
}
</style>
