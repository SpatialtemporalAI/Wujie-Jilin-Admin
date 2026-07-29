<script setup lang="ts">
import { computed } from 'vue';
import { useThemeStore } from '@/store/modules/theme';
import { $t } from '@/locales';

defineOptions({
  name: 'GlobalLogo'
});

interface Props {
  /** Whether to show the title */
  showTitle?: boolean;
}

withDefaults(defineProps<Props>(), {
  showTitle: true
});

const themeStore = useThemeStore();

const logoClass = computed(() => ({
  'w-full flex-center nowrap-hidden': true,
  'bg-#4576f5': themeStore.isLightSider
}));
</script>

<template>
  <RouterLink to="/" :class="logoClass">
    <img src="@/assets/imgs/logo2.png" alt="" class="mr-4px h-24px w-24px object-contain" />
    <h2
      v-show="showTitle"
      class="pl-8px text-16px font-bold transition duration-300 ease-in-out"
      :class="themeStore.isLightSider ? 'text-#fff' : 'text-#pimary'"
    >
      {{ $t('system.title') }}
    </h2>
  </RouterLink>
</template>

<style scoped></style>
