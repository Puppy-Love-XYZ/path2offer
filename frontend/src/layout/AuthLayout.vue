<template>
  <div class="auth-layout">
  
    <div class="auth-orb auth-orb-1" />
    <div class="auth-orb auth-orb-2" />
    <div class="auth-orb auth-orb-3" />

    <div class="auth-grid" />
    <slot />
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100vh;
  background: linear-gradient(145deg, #1e1b4b 0%, #312e81 35%, #1e3a5f 70%, #0c1a2e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}


.auth-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(99, 102, 241, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(99, 102, 241, 0.06) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
}


.auth-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  animation: orb-drift 12s ease-in-out infinite alternate;
}

.auth-orb-1 {
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.35) 0%, transparent 70%);
  top: -120px;
  left: -80px;
  animation-duration: 14s;
}

.auth-orb-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, transparent 70%);
  bottom: -80px;
  right: -60px;
  animation-duration: 10s;
  animation-delay: -3s;
}

.auth-orb-3 {
  width: 280px;
  height: 280px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, transparent 70%);
  top: 40%;
  left: 55%;
  animation-duration: 16s;
  animation-delay: -6s;
}

@keyframes orb-drift {
  0%   { transform: translate(0, 0) scale(1); }
  33%  { transform: translate(30px, -20px) scale(1.05); }
  66%  { transform: translate(-20px, 30px) scale(0.96); }
  100% { transform: translate(15px, -10px) scale(1.02); }
}
</style>
