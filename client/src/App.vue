<script setup>
import { useRoute } from 'vue-router'

</script>

<template>
  <div class="container-fluid">
    <nav class="navbar navbar-expand-sm bg-body-tertiary">
      <div class="container-fluid">
        <a class="navbar-brand" href="#"><b>GYM</b></a>

        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavDropdown"
          aria-controls="navbarNavDropdown" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNavDropdown">
          <ul class="navbar-nav me-auto">            
            <li class="nav-item">
              <router-link class="nav-link" to="/">Пользователи</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/memberships">Абонементы</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/membershiptypes">Типы абонементов</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/workoutsessions">Тренировки</router-link>
            </li>
          </ul>

          <ul class="navbar-nav">
            <li class="navbar-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown"
                aria-expanded="false">
                Админка
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li><a href="/admin" class="dropdown-item">Админка</a></li>
              </ul>
            </li>
          </ul>

        </div>
      </div>
    </nav>
  </div>

  <div class="container-fluid">
    <router-view />
  </div>
</template>

<style>
.navbar .nav-link.active {
  font-weight: 600;
}
</style>
