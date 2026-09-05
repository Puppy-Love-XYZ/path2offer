<template>
  <div class="register-card" :class="{ 'card-enter': mounted }">

    <div class="register-header">
      <div class="logo-ring">
        <img src="../assets/logo.png" alt="logo" class="register-logo" />
      </div>
      <h1 class="register-title">创建账号</h1>
      <p class="register-subtitle">加入 Path2Offer，开启智能求职之旅</p>
    </div>

    <div class="register-divider">
      <span>填写注册信息</span>
    </div>

   
    <el-form :model="form" :rules="rules" ref="formRef" class="register-form">
      <el-form-item prop="username">
        <el-input
          v-model="form.username"
          placeholder="请输入用户名（2-50位）"
          size="large"
          :prefix-icon="User"
          clearable
        />
      </el-form-item>

      <el-form-item prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请设置密码"
          size="large"
          :prefix-icon="Lock"
          show-password
        />
      </el-form-item>

      
      <Transition name="rules-fade">
        <div class="pwd-rules" v-if="form.password">
          <div class="pwd-rule" v-for="rule in passwordRules" :key="rule.key" :class="rule.passed ? 'pass' : 'fail'">
            <el-icon><Check v-if="rule.passed" /><Close v-else /></el-icon>
            <span>{{ rule.label }}</span>
          </div>
        </div>
      </Transition>

      <el-form-item prop="confirmPassword">
        <el-input
          v-model="form.confirmPassword"
          type="password"
          placeholder="请再次输入密码"
          size="large"
          :prefix-icon="Lock"
          show-password
        />
        <Transition name="rules-fade">
          <div v-if="form.confirmPassword && form.password !== form.confirmPassword" class="pwd-mismatch">
            两次密码不一致
          </div>
        </Transition>
      </el-form-item>

      <button
        type="button"
        class="register-btn"
        :class="{ loading: loading }"
        :disabled="!canSubmit || loading"
        @click="handleRegister"
      >
        <span v-if="!loading" class="btn-text">
          <el-icon><UserFilled /></el-icon>
          立即注册
        </span>
        <span v-else class="btn-text">
          <span class="btn-spinner"></span>
          注册中...
        </span>
        <span class="btn-shimmer" />
      </button>
    </el-form>

    <div class="register-footer">
      <span>已有账号？</span>
      <span class="footer-link" @click="router.push('/login')">立即登录 →</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Check, Close, UserFilled } from '@element-plus/icons-vue'
import { apiRegister } from '../api/auth'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { login } = useAuth()
const formRef = ref()
const loading = ref(false)
const mounted = ref(false)

onMounted(() => setTimeout(() => { mounted.value = true }, 80))

const form = reactive({ username: '', password: '', confirmPassword: '' })

function hasSequentialChars(pwd: string, len = 6): boolean {
  for (let i = 0; i <= pwd.length - len; i++) {
    const win = pwd.slice(i, i + len)
    const diffs = Array.from({ length: len - 1 }, (_, j) => win.charCodeAt(j + 1) - win.charCodeAt(j))
    if (diffs.every(d => d === 1) || diffs.every(d => d === -1)) return true
  }
  return false
}

const passwordRules = computed(() => {
  const p = form.password
  return [
    { key: 'length',   label: '长度 8-20 位',         passed: p.length >= 8 && p.length <= 20 },
    { key: 'letter',   label: '包含字母',               passed: /[a-zA-Z]/.test(p) },
    { key: 'digit',    label: '包含数字',               passed: /[0-9]/.test(p) },
    { key: 'special',  label: '包含特殊符号',           passed: /[!@#$%^&*()\-_=+\[\]{};:'",.<>/?\\|`~]/.test(p) },
    { key: 'noRepeat', label: '无 4+ 连续相同字符',    passed: !/(.)\1{3,}/.test(p) },
    { key: 'noSeq',    label: '无 6+ 连续顺序字符',    passed: !hasSequentialChars(p) },
  ]
})

const allRulesPassed = computed(() => passwordRules.value.every(r => r.passed))
const canSubmit = computed(() =>
  form.username.length >= 2 &&
  allRulesPassed.value &&
  form.password === form.confirmPassword &&
  form.confirmPassword.length > 0
)

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度 2-50 位', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请设置密码', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请确认密码', trigger: 'blur' }],
}

async function handleRegister() {
  if (!canSubmit.value) return
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      const res = await apiRegister(form.username, form.password)
      login(res.access_token, res.user)
      ElMessage.success('注册成功，欢迎加入！')
      router.push('/profile?welcome=1')
    } catch (e: any) {
      ElMessage.error(e.message || '注册失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>

.register-card {
  width: 460px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 20px;
  padding: 36px 40px;
  box-shadow:
    0 0 0 1px rgba(99, 102, 241, 0.1),
    0 24px 64px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.55s ease, transform 0.55s ease;
}

.register-card.card-enter {
  opacity: 1;
  transform: translateY(0);
}

.register-header {
  text-align: center;
  margin-bottom: 22px;
}

.logo-ring {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(139, 92, 246, 0.3));
  border: 1.5px solid rgba(99, 102, 241, 0.4);
  margin-bottom: 12px;
  box-shadow: 0 0 24px rgba(99, 102, 241, 0.3);
  animation: logo-glow 3s ease-in-out infinite alternate;
}

@keyframes logo-glow {
  from { box-shadow: 0 0 16px rgba(99, 102, 241, 0.25); }
  to   { box-shadow: 0 0 32px rgba(99, 102, 241, 0.5); }
}

.register-logo { width: 36px; height: 36px; }

.register-title {
  color: #fff;
  font-size: 22px;
  font-weight: 800;
  margin: 0 0 4px;
  background: linear-gradient(135deg, #e0e7ff, #c7d2fe, #a5b4fc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-subtitle {
  color: rgba(199, 210, 254, 0.55);
  font-size: 12px;
  margin: 0;
}


.register-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.register-divider::before,
.register-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(99, 102, 241, 0.2);
}

.register-divider span {
  color: rgba(199, 210, 254, 0.5);
  font-size: 12px;
  white-space: nowrap;
}

/* ── 表单 ── */
.register-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.register-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(99, 102, 241, 0.2);
  box-shadow: none;
  border-radius: 10px;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
}

.register-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(99, 102, 241, 0.45);
  background: rgba(255, 255, 255, 0.1);
}

.register-form :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.register-form :deep(.el-input__inner) { color: #fff; font-size: 14px; }
.register-form :deep(.el-input__inner::placeholder) { color: rgba(199, 210, 254, 0.4); }
.register-form :deep(.el-input__prefix-inner .el-icon),
.register-form :deep(.el-input__suffix-inner .el-icon) { color: rgba(165, 180, 252, 0.6); }


.pwd-rules {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin: -6px 0 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.pwd-rule {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  transition: color 0.2s;
}

.pwd-rule.pass { color: #86efac; }
.pwd-rule.fail { color: rgba(199, 210, 254, 0.35); }

.rules-fade-enter-active,
.rules-fade-leave-active { transition: opacity 0.25s, transform 0.25s; }
.rules-fade-enter-from,
.rules-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.pwd-mismatch {
  color: #fca5a5;
  font-size: 12px;
  margin-top: 4px;
}


.register-btn {
  width: 100%;
  height: 46px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #7c3aed 100%);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 2px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  margin-top: 2px;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(99, 102, 241, 0.55);
}

.register-btn:active:not(:disabled) { transform: translateY(0); }

.register-btn:disabled {
  opacity: 0.45;
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
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.18) 50%, transparent 60%);
  transform: translateX(-100%);
}

.register-btn:hover:not(:disabled) .btn-shimmer {
  transform: translateX(100%);
  transition: transform 0.5s ease;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin { to { transform: rotate(360deg); } }

.register-footer {
  text-align: center;
  color: rgba(199, 210, 254, 0.5);
  font-size: 14px;
  margin-top: 14px;
}

.footer-link {
  color: #a5b4fc;
  font-weight: 600;
  cursor: pointer;
  margin-left: 4px;
  transition: color 0.2s;
}

.footer-link:hover { color: #c7d2fe; }
</style>
