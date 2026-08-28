<script setup lang="ts">
import { ref } from 'vue';
import { NButton, NCard, NEmpty, NPopconfirm, NSpace, NSpin, NTag, useMessage } from 'naive-ui';
import { fetchDeleteRobot, fetchGetRobotList, fetchGetRobotSlotStatus, fetchRestartRobotSlot } from '@/service/api';
import { useAuth } from '@/hooks/business/auth';
import { $t } from '@/locales';
import SvgIcon from '@/components/custom/svg-icon.vue';
import RobotOperateDrawer from './modules/robot-operate-drawer.vue';
import RobotStatusDrawer from './modules/robot-status-drawer.vue';
import RobotGrpcConfigDrawer from './modules/robot-grpc-config-drawer.vue';

defineOptions({ name: 'RobotManagePage' });

const { hasAuth } = useAuth();
const message = useMessage();

/** 机器人列表 */
const robotList = ref<Api.Robot.Robot[]>([]);
const loading = ref(false);

/** 状态抽屉 */
const statusDrawerVisible = ref(false);
const statusDrawerRobotId = ref<number | null>(null);

/** gRPC 配置抽屉 */
const grpcDrawerVisible = ref(false);
const grpcDrawerRobotId = ref<number | null>(null);

/** 机器人操作抽屉 */
const robotDrawerVisible = ref(false);
const robotOperateType = ref<NaiveUI.TableOperateType>('add');
const editingRobotData = ref<Api.Robot.Robot | null>(null);

async function loadData() {
  loading.value = true;
  try {
    const { data, error } = await fetchGetRobotList({ page: 1, page_size: 200 });
    if (!error && data) {
      robotList.value = data.records || [];
      loadSlotStatuses(data.records || []);
    }
  } catch (err) {
    console.error('加载机器人列表失败:', err);
  } finally {
    loading.value = false;
  }
}

/** 服务器自启状态（面板返回：已启动/启动中/启动失败/未配置/未知） */
const slotStatusMap = ref<Record<number, string>>({});
const slotRestartingMap = ref<Record<number, boolean>>({});

/** 并行拉取每台机器人的自启状态，单台失败置「未知」不影响其它卡片 */
function loadSlotStatuses(records: Api.Robot.Robot[]) {
  records.forEach(robot => {
    loadSlotStatus(robot.id);
  });
}

async function loadSlotStatus(robotId: number) {
  try {
    const { data, error } = await fetchGetRobotSlotStatus(robotId);
    slotStatusMap.value[robotId] = !error && data ? data.status : '未知';
  } catch {
    slotStatusMap.value[robotId] = '未知';
  }
}

function getSlotStatusType(status: string): import('naive-ui').TagProps['type'] {
  const typeMap: Record<string, import('naive-ui').TagProps['type']> = {
    已启动: 'success',
    启动中: 'warning',
    启动失败: 'error'
  };
  return typeMap[status] || 'default';
}

async function handleRestartSlot(robot: Api.Robot.Robot) {
  slotRestartingMap.value[robot.id] = true;
  try {
    const { data, error } = await fetchRestartRobotSlot(robot.id);
    if (!error && data) {
      slotStatusMap.value[robot.id] = data.status;
      message.success(`重启指令已下发，当前状态：${data.status}`);
    }
  } catch (err) {
    console.error('重启服务器自启失败:', err);
  } finally {
    slotRestartingMap.value[robot.id] = false;
    loadSlotStatus(robot.id);
  }
}

function handleAddRobot() {
  robotOperateType.value = 'add';
  editingRobotData.value = null;
  robotDrawerVisible.value = true;
}

function handleEditRobot(row: Api.Robot.Robot) {
  robotOperateType.value = 'edit';
  editingRobotData.value = row;
  robotDrawerVisible.value = true;
}

function handleViewStatus(row: Api.Robot.Robot) {
  statusDrawerRobotId.value = row.id;
  statusDrawerVisible.value = true;
}

function handleEditGrpc(row: Api.Robot.Robot) {
  grpcDrawerRobotId.value = row.id;
  grpcDrawerVisible.value = true;
}

async function handleDelete(id: number) {
  try {
    await fetchDeleteRobot(id);
    message.success($t('common.deleteSuccess'));
    loadData();
  } catch (error) {
    console.error('删除机器人失败:', error);
  }
}

function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    online: '在线',
    offline: '离线',
    inactive: '未激活',
    busy: '忙碌',
    charging: '充电中',
    error: '故障'
  };
  return statusMap[status] || status || '未知';
}

function getStatusType(status: string): import('naive-ui').TagProps['type'] {
  const typeMap: Record<string, import('naive-ui').TagProps['type']> = {
    online: 'success',
    offline: 'default',
    inactive: 'default',
    busy: 'warning',
    charging: 'info',
    error: 'error'
  };
  return typeMap[status] || 'default';
}

loadData();
</script>

<template>
  <div class="min-h-500px flex-col-stretch gap-16px overflow-hidden lt-sm:overflow-auto">
    <NCard title="机器人管理" :bordered="false" size="small" class="card-wrapper sm:flex-1-hidden">
      <template #header-extra>
        <NSpace>
          <NButton v-if="hasAuth('robot:manage:add')" type="primary" ghost size="small" @click="handleAddRobot">
            <template #icon>
              <icon-ic-round-plus class="text-icon" />
            </template>
            {{ $t('common.add') }}
          </NButton>
          <NButton size="small" :loading="loading" @click="loadData">
            <template #icon>
              <icon-mdi-refresh class="text-icon" :class="{ 'animate-spin': loading }" />
            </template>
            {{ $t('common.refresh') }}
          </NButton>
        </NSpace>
      </template>

      <NSpin :show="loading">
        <div v-if="robotList.length === 0" class="py-40px">
          <NEmpty description="暂无机器人数据" />
        </div>
        <div v-else class="robot-card-grid">
          <div v-for="robot in robotList" :key="robot.id" class="robot-card card-wrapper">
            <div class="robot-card-header">
              <div class="robot-logo">
                <img v-if="robot.logo" :src="robot.logo" alt="logo" />
                <div v-else class="robot-logo-placeholder">
                  <SvgIcon icon="mdi:robot" class="text-32px" />
                </div>
              </div>
              <div class="robot-title">
                <div class="robot-name">{{ robot.name }}</div>
                <div class="robot-serial">{{ robot.serial_number }}</div>
              </div>
              <NTag :type="getStatusType(robot.status as string)" size="small" round>
                {{ getStatusText(robot.status as string) }}
              </NTag>
            </div>

            <div class="robot-card-body">
              <div class="robot-info-item">
                <span class="robot-info-label">型号：</span>
                <span class="robot-info-value">{{ robot.model_name || '-' }}</span>
              </div>
              <div class="robot-info-item">
                <span class="robot-info-label">地图：</span>
                <span class="robot-info-value">{{ robot.map_name || '-' }}</span>
              </div>
            </div>

            <div class="robot-card-slot" v-if="hasAuth('robot:manage:restart')">
              <span class="robot-info-label">服务器自启状态</span>
              <NSpace align="center">
                <NTag :type="getSlotStatusType(slotStatusMap[robot.id] || '未知')" size="small" round>
                  {{ slotStatusMap[robot.id] || '未知' }}
                </NTag>
                <NButton size="small" secondary :loading="slotRestartingMap[robot.id]"
                  :disabled="slotStatusMap[robot.id] === '启动中'" @click="handleRestartSlot(robot)">
                  <template #icon>
                    <icon-mdi-restart class="text-icon" />
                  </template>
                  重启
                </NButton>
              </NSpace>
            </div>

            <div class="robot-card-footer">
              <NSpace>
                <NButton v-if="hasAuth('robot:manage:edit')" type="primary" ghost size="small"
                  @click="handleEditRobot(robot)">
                  {{ $t('common.edit') }}
                </NButton>
                <NButton v-if="hasAuth('robot:manage:grpc_config')" type="info" ghost size="small"
                  @click="handleEditGrpc(robot)">
                  gRPC配置
                </NButton>
                <NButton v-if="hasAuth('robot:manage:list')" class="hidden" ghost size="small"
                  @click="handleViewStatus(robot)">
                  状态
                </NButton>
                <NPopconfirm v-if="hasAuth('robot:manage:delete')" @positive-click="handleDelete(robot.id)">
                  <template #trigger>
                    <NButton type="error" ghost size="small">
                      {{ $t('common.delete') }}
                    </NButton>
                  </template>
                  {{ $t('common.confirmDelete') }}
                </NPopconfirm>
              </NSpace>
            </div>
          </div>
        </div>
      </NSpin>

      <RobotOperateDrawer v-model:visible="robotDrawerVisible" :operate-type="robotOperateType"
        :row-data="editingRobotData" @submitted="loadData" />
      <RobotStatusDrawer v-model:visible="statusDrawerVisible" :robot-id="statusDrawerRobotId" />
      <RobotGrpcConfigDrawer v-model:visible="grpcDrawerVisible" :robot-id="grpcDrawerRobotId" @submitted="loadData" />
    </NCard>
  </div>
</template>

<style scoped>
.robot-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 8px 16px;
}

.robot-card {
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid var(--n-border-color);
  /* background-color: var(--n-card-color); */
  background-color: #fff;
  transition: box-shadow 0.2s ease;
}

.robot-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.robot-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.robot-logo {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background-color: var(--n-action-color);
}

.robot-logo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.robot-logo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--n-text-color-disabled);
}

.robot-title {
  flex: 1;
  min-width: 0;
}

.robot-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--n-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.robot-serial {
  font-size: 12px;
  color: var(--n-text-color-disabled);
  margin-top: 4px;
}

.robot-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.robot-info-item {
  display: flex;
  align-items: center;
  font-size: 13px;
}

.robot-info-label {
  color: var(--n-text-color-disabled);
  flex-shrink: 0;
}

.robot-info-value {
  color: var(--n-text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.robot-card-slot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  margin-bottom: 4px;
  border-top: 1px dashed var(--n-divider-color);
  font-size: 13px;
}

.robot-card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid var(--n-divider-color);
}

@media (max-width: 640px) {
  .robot-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
