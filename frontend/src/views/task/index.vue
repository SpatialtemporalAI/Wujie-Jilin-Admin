<script setup lang="ts">
import { ref } from 'vue';
import TaskListTab from './modules/task-list-tab.vue';
import TaskExecutionTab from './modules/task-execution-tab.vue';
import TaskHistoryTab from './modules/task-history-tab.vue';

defineOptions({ name: 'TaskPage' });

const activeTab = ref('list');
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard :bordered="false" size="small" class="flex-1-hidden card-wrapper">
      <NTabs
        v-model:value="activeTab"
        type="line"
        animated
        class="h-full min-h-0 flex flex-col"
        pane-wrapper-class="min-h-0 flex-1"
        pane-class="h-full min-h-0"
      >
        <NTabPane name="list" tab="任务列表">
          <TaskListTab />
        </NTabPane>
        <NTabPane name="execution" tab="执行列表">
          <TaskExecutionTab />
        </NTabPane>
        <NTabPane name="history" tab="历史任务">
          <TaskHistoryTab />
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
</template>

<style scoped></style>
