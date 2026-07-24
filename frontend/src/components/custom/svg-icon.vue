<script setup lang="ts">
import { computed, useAttrs } from 'vue';
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
  'material-symbols:notifications-outline': 'notifications-outline',
  'material-symbols:cloud-download-outline': 'cloud-download-outline',
  'ph:user-circle': 'user-circle',
  'ph:sign-out': 'sign-out',
  'mdi:book-alphabet': 'book-alphabet',
  'mdi:upload': 'upload',
  'arcticons:example': 'example',
  'mdi:chart-areaspline-variant': 'chart-areaspline-variant',
  'mdi:cog': 'cog',
  'mdi:menu': 'menu',
  'mdi:robot': 'robot'
};

/** All local SVG icons available (filenames without .svg extension) */
const localIcons = new Set([
  'activity', 'api', 'application-cog-outline', 'at-sign', 'avatar', 'banner',
  'bar-chart-outlined', 'book-alphabet', 'cast', 'chart-areaspline-variant',
  'chevron-down', 'chevron-up', 'chip', 'chrome', 'clipboard-check-outline',
  'clipboard-list-outline', 'clock-outline', 'cloud-download-outline', 'cog', 'config', 'copy',
  'custom-icon', 'dashboadr', 'demo', 'document-download', 'download',
  'empty-data', 'example', 'expectation', 'face-recognition',
  'file-document-outline', 'hdr-auto', 'heart', 'history', 'information-outline',
  'language', 'language-python', 'logo', 'map-outline', 'menu', 'menu-fold-left',
  'menu-fold-right', 'money-collect-outlined', 'monitor-dashboard', 'monitor-eye',
  'network-error', 'nightlight-rounded', 'no-icon', 'no-permission', 'not-found',
  'ph-caret-double-left-bold', 'ph-caret-double-right-bold', 'pin', 'pin-off',
  'notifications-outline', 'robot', 'schedule-outline', 'service-error', 'set', 'sign-out', 'store-outline', 'sunny',
  'user-circle',
  'task-alt-outline', 'trademark-circle-outlined', 'upload', 'volume-high', 'wind'
]);

const bindAttrs = computed<{ class: string; style: string }>(() => ({
  class: (attrs.class as string) || '',
  style: (attrs.style as string) || ''
}));

/**
 * Auto-detect local icon name from Iconify icon name
 * Priority: explicit mapping > icon name after ':'
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

/** Check if local icon file exists (compile-time check, no DOM needed) */
const localIconExists = computed(() => {
  if (!localIconName.value) return false;
  return localIcons.has(localIconName.value);
});

const renderLocalIcon = computed(() => {
  // If we have a local icon name and it exists in our local set, render local
  if (localIconName.value && localIconExists.value) {
    return true;
  }
  // No local icon available: render Iconify if icon prop provided, else fallback to no-icon
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
