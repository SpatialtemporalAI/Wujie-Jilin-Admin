<script setup lang="ts">
import { ref } from 'vue';
import logoPng from '@/assets/imgs/logo2.png';

defineOptions({ name: 'AboutUs' });

const showModal = ref(false);
</script>

<template>
  <div>
    <ButtonIcon icon="mdi:information-outline" tooltip-content="关于我们" @click="showModal = true" />

    <NModal v-model:show="showModal" preset="card" title="关于我们" style="width: 660px; max-width: 90vw;" :bordered="false">
      <div class="flex-col gap-16px mt-12px">
        <div class="about-banner">
          <img :src="logoPng" alt="logo" class="about-logo" />
          <div class="flex-col gap-4px">
            <div class="about-title">机器人管理平台 · 吉大二院</div>
            <div class="about-meta">版本号：v1.0.0</div>
            <div class="about-meta">版本更新：2026-07-04</div>
          </div>
        </div>

        <div class="about-desc bg-[#f3f4f6] dark:bg-[#1f2937] text-[#6b7280] dark:text-[#9ca3af]">
          本平台为医院场景下的人形具身智能机器人提供全面的后台管理与控制能力，集成地图管理、任务调度、参数配置、运行监控等核心模块，实现机器人集群的高效协同与可视化运维。
        </div>
        <n-divider></n-divider>
        <div class="text-#999 text-center mb-12px">技术支持:无界智慧(珠海)科技有限公司</div>
      </div>
    </NModal>
  </div>
</template>

<style scoped>
.about-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
  color: #fff;
}

.about-logo {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  object-fit: contain;
  padding: 8px;
  flex-shrink: 0;
}

.about-title {
  font-size: 16px;
  font-weight: 600;
}

.about-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

.about-desc {
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
}
</style>
