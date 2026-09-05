import { createApp } from 'vue'
import './style.css'
import './assets/styles/pure-professional.css'
import ElementPlus from 'element-plus'
import router from './router' 
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.use(router) 
app.mount('#app')