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
    <Simplebar class="h-full" :style="scrollbarStyle" :class="{'light': props.blueBg}">
      <slot />
    </Simplebar>
  </div>
</template>

<style scoped lang="scss">
.light{
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
