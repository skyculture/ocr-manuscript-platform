import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Annotation from '../views/Annotation.vue'
import Training from '../views/Training.vue'
import Proofreading from '../views/Proofreading.vue'
import Chat from '../views/Chat.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/annotation', name: 'Annotation', component: Annotation },
  { path: '/training', name: 'Training', component: Training },
  { path: '/proofreading', name: 'Proofreading', component: Proofreading },
  { path: '/chat', name: 'Chat', component: Chat }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
