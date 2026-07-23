<script setup lang="ts">
import { computed, onMounted, ref, useAttrs, watch } from 'vue';
import { Icon } from '@iconify/vue';

defineOptions({ name: 'SvgIcon', inheritAttrs: false });

/**
 * Props
 *
 * - Support iconify and local svg icon
 * - If icon and localIcon are passed at the same time, localIcon will be rendered first
 * - If the local SVG icon is missing, fall back to the Iconify remote icon
 */
interface Props {
  /** Iconify icon name */
  icon?: string;
  /** Local svg icon name */
  localIcon?: string;
}

const props = defineProps<Props>();

const attrs = useAttrs();

/** Map Iconify icon names to local SVG icon names (explicit mappings override auto-detection) */
const iconToLocalIconMap: Record<string, string> = {
  'mdi:monitor-dashboard': 'monitor-dashboard',
  'mdi:map-outline': 'map-outline',
  'mdi:clipboard-check-outline': 'clipboard-check-outline',
  'mdi:api': 'api',
  'mdi:store-outline': 'store-outline',
  'mdi:clipboard-list-outline': 'clipboard-list-outline',
  'icon-park-outline:config': 'config',
  'mdi:monitor-eye': 'monitor-eye',
  'mdi:file-document-outline': 'file-document-outline',
  'mdi:face-recognition': 'face-recognition',
  'material-symbols:schedule-outline': 'schedule-outline',
  'material-symbols:task-alt-outline': 'task-alt-outline',
  'material-symbols:history': 'history',
  'mdi:book-alphabet': 'book-alphabet',
  'mdi:upload': 'upload',
  'arcticons:example': 'example',
  'mdi:chart-areaspline-variant': 'chart-areaspline-variant',
  'mdi:cog': 'cog',
  'mdi:menu': 'menu',
  'mdi:robot': 'robot'
};

const bindAttrs = computed<{ class: string; style: string }>(() => ({
  class: (attrs.class as string) || '',
  style: (attrs.style as string) || ''
}));

/**
 * Auto-detect local icon name from Iconify icon name
 * Priority: explicit mapping > icon name after ':'
 * Examples:
 *   'mdi:information-outline' -> 'information-outline'
 *   'heroicons:language' -> 'language'
 *   'ph-caret-double-left-bold' -> 'ph-caret-double-left-bold' (no colon, use full)
 */
function getLocalIconName(icon: string): string | null {
  if (!icon) return null;
  // Check explicit mapping first
  if (iconToLocalIconMap[icon]) return iconToLocalIconMap[icon];
  // Auto-detect: try the part after ':' if exists
  if (icon.includes(':')) {
    return icon.split(':').pop() || null;
  }
  // No colon, use the full icon name as-is
  return icon;
}

const localIconName = computed(() => {
  // Explicit localIcon prop takes highest priority
  if (props.localIcon) return props.localIcon;
  // Auto-detect from icon prop
  return getLocalIconName(props.icon || '');
});

const { VITE_ICON_LOCAL_PREFIX: prefix } = import.meta.env;

const symbolId = computed(() => `#${prefix}-${localIconName.value || 'no-icon'}`);

const localIconExists = ref(false);

function checkLocalIconExists() {
  if (!localIconName.value) {
    localIconExists.value = false;
    return;
  }

  const id = `${prefix}-${localIconName.value}`;
  localIconExists.value = !!document.getElementById(id);
}

onMounted(checkLocalIconExists);
watch(localIconName, checkLocalIconExists);

const renderLocalIcon = computed(() => {
  // If we have a local icon name, check if it exists in DOM
  if (localIconName.value) {
    return localIconExists.value;
  }
  // No local icon: render Iconify if icon prop provided, else fallback to no-icon
  return !props.icon;
});
</script>

<template>
  <template v-if="renderLocalIcon">
    <svg aria-hidden="true" width="1em" height="1em" v-bind="bindAttrs">
      <use :xlink:href="symbolId" fill="currentColor" />
    </svg>
  </template>
  <template v-else>
    <Icon v-if="icon" :icon="icon" v-bind="bindAttrs" />
  </template>
</template>

<style scoped></style>
