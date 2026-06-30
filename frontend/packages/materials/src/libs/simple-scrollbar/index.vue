<script setup lang="ts">
import { computed } from 'vue';
import Simplebar from 'simplebar-vue';
import 'simplebar-vue/dist/simplebar.min.css';

defineOptions({
  name: 'SimpleScrollbar'
});

interface Props {
  /** 是否在白天非深色模式下显示蓝色背景 */
  blueBg?: boolean;
  /** 是否为深色模式 */
  darkMode?: boolean;
}

const props = defineProps<Props>();

const scrollbarStyle = computed(() => {
  if (props.blueBg) {
    return { backgroundColor: '#3761d2' };
  }
  return {};
});
</script>

<template>
  <div class="h-full flex-1-hidden">
    <Simplebar class="h-full" :style="scrollbarStyle" :class="{'light': props.blueBg, 'dark': props.darkMode}">
      <slot />
    </Simplebar>
  </div>
</template>

<style scoped lang="scss">
:deep(.simplebar-scrollbar::before) {
  background: rgba(128, 128, 128, 0.6) !important;
}

.dark {
  :deep(.simplebar-scrollbar::before) {
    background: rgba(255, 255, 255, 0.5) !important;
  }
}

.light {
  :deep(.simplebar-scrollbar::before) {
    background: rgba(255, 255, 255, 0.7) !important;
  }

  :deep(.n-menu-item-content--child-active) {
    background-color: #4576f5;

    &:hover {
      &::before {
        background-color: #4576f5 !important;
      }

      .n-menu-item-content__icon {
        color: #fff !important;
      }

      .n-menu-item-content-header {
        color: #fff !important;
      }

      .n-menu-item-content__arrow {
        color: #fff !important;
      }
    }
  }
}
</style>
