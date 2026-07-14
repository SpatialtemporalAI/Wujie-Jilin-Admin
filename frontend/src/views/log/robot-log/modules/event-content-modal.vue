<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { NModal, NSwitch } from 'naive-ui';

interface Props {
  visible: boolean;
  content: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void;
}>();

const viewParsed = ref(true);

const parsedContent = computed<string | null>(() => {
  if (!props.content) return null;
  try {
    const parsed = JSON.parse(props.content);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return null;
  }
});

const isJson = computed(() => parsedContent.value !== null);

const displayContent = computed(() => {
  if (viewParsed.value && parsedContent.value !== null) {
    return parsedContent.value;
  }
  return props.content;
});

function close() {
  emit('update:visible', false);
}

watch(
  () => props.visible,
  visible => {
    if (visible) {
      viewParsed.value = isJson.value;
    }
  },
  { immediate: true }
);
</script>

<template>
  <NModal
    :show="visible"
    preset="card"
    title="事件内容详情"
    class="w-800px max-w-90vw"
    :block-scroll="false"
    @update:show="close"
  >
    <div class="mb-16px flex items-center gap-12px">
      <span class="text-14px text-gray-600 dark:text-gray-300">查看方式：</span>
      <NSwitch v-model:value="viewParsed" :disabled="!isJson">
        <template #checked>解析内容</template>
        <template #unchecked>原始内容</template>
      </NSwitch>
      <span v-if="!isJson" class="text-12px text-gray-400">（当前内容非 JSON 格式）</span>
    </div>
    <div
      class="max-h-60vh overflow-auto rounded-lg bg-#f5f5f5 p-16px dark:bg-#1a1a1a"
    >
      <pre class="whitespace-pre-wrap break-all text-13px text-#333 dark:text-#eee">{{ displayContent }}</pre>
    </div>
  </NModal>
</template>
