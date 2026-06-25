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
    <Simplebar class="h-full" :style="scrollbarStyle">
      <slot />
    </Simplebar>
  </div>
</template>

<style scoped>
:deep(.n-menu .n-menu-item-content.n-menu-item-content--selected::before) {
  background-color: #ffffff;
}
</style>
