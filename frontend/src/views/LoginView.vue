<template>
  <div class="login-card" :class="{ 'card-enter': mounted }">
    <div class="login-header">
      <div class="logo-ring">
        <img src="../assets/logo.png" alt="logo" class="login-logo" />
      </div>
      <h1 class="login-title">Path2Offer</h1>
      <p class="login-subtitle">智能化就业决策辅助系统</p>
    </div>

    <div class="login-divider">
      <span>登录账号</span>
    </div>

    <el-form :model="form" :rules="rules" ref="formRef" class="login-form" @submit.prevent="handleLogin">
      <el-form-item prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名" size="large" :prefix-icon="User" clearable
          @keyup.enter="handleLogin" />
      </el-form-item>
      <el-form-item prop="password">
        <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" :prefix-icon="Lock"
          show-password @keyup.enter="handleLogin" />
      </el-form-item>

      <button type="button" class="login-btn" :class="{ loading: loading }" :disabled="loading" @click="handleLogin">
        <span v-if="!loading" class="btn-text">
          <el-icon>
            <Right />
          </el-icon>
          登 录
        </span>
        <span v-else class="btn-text">
          <span class="btn-spinner"></span>
          登录中...
        </span>
        <span class="btn-shimmer" />
      </button>
    </el-form>

    <div class="login-footer">
      <span>还没有账号？</span>
      <span class="footer-link" @click="router.push('/register')">立即注册 →</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Right } from '@element-plus/icons-vue'
import { apiLogin } from '../api/auth'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()
const formRef = ref()
const loading = ref(false)
const mounted = ref(false)

onMounted(() => setTimeout(() => { mounted.value = true }, 50))

const form = reactive({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await apiLogin(form.username, form.password)
      login(res.access_token, res.user)
      ElMessage.success('登录成功')
      router.push('/')
    } catch (e: any) {
      ElMessage.error(e.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 20px;
  padding: 40px;
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.1),
    0 24px 64px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.login-card.card-enter {
  opacity: 1;
  transform: translateY(0);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.logo-ring {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  border: 1.5px solid rgba(99, 102, 241, 0.4);
  margin-bottom: 14px;
  box-shadow: 0 0 24px rgba(99, 102, 241, 0.3);
  animation: logo-glow 3s ease-in-out infinite alternate;
}

@keyframes logo-glow {
  from {
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
  }

  to {
    box-shadow: 0 0 32px rgba(99, 102, 241, 0.5);
  }
}

.login-logo {
  width: 40px;
  height: 40px;
}

.login-title {
  color: #fff;
  font-size: 26px;
  font-weight: 800;
  margin: 0 0 4px;
  letter-spacing: -0.3px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  color: rgba(199, 210, 254, 0.6);
  font-size: 13px;
  margin: 0;
}

.login-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.login-divider::before,
.login-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(99, 102, 241, 0.2);
}

.login-divider span {
  color: rgba(199, 210, 254, 0.5);
  font-size: 12px;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.login-form {
  margin-bottom: 16px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
  border-radius: 10px;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(99, 102, 241, 0.45);
  background: rgba(255, 255, 255, 0.1);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.login-form :deep(.el-input__inner) {
  color: #fff;
  font-size: 14px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(199, 210, 254, 0.4);
}

.login-form :deep(.el-input__prefix-inner .el-icon),
.login-form :deep(.el-input__suffix-inner .el-icon) {
  color: rgba(165, 180, 252, 0.6);
}

.login-btn {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #7c3aed 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 3px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  margin-top: 4px;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(99, 102, 241, 0.55);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-text {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255, 255, 255, 0.18) 50%, transparent 60%);
  transform: translateX(-100%);
  transition: transform 0s;
}

.login-btn:hover:not(:disabled) .btn-shimmer {
  transform: translateX(100%);
  transition: transform 0.5s ease;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  text-align: center;
  color: rgba(199, 210, 254, 0.5);
  font-size: 14px;
}

.footer-link {
  color: #a5b4fc;
  font-weight: 600;
  cursor: pointer;
  margin-left: 4px;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #c7d2fe;
}
</style>