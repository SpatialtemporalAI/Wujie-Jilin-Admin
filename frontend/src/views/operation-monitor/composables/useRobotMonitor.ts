import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { fetchGetAllRobots, fetchGetLatestRobotStatus } from '@/service/api';

export interface ParsedLocation {
  x: number;
  y: number;
  angle: number;
}

const POLL_INTERVAL = 3000;

export function useRobotMonitor() {
  const selectedRobotId = ref<number | null>(null);
  const robotList = ref<Api.Robot.AllRobot[]>([]);
  const latestStatus = ref<Api.Robot.RobotStatusRecord | null>(null);
  const loading = ref(false);

  let pollingTimer: ReturnType<typeof setInterval> | null = null;

  const selectedRobot = computed(() => robotList.value.find(r => r.id === selectedRobotId.value) ?? null);

  const parsedLocation = computed<ParsedLocation | null>(() => {
    const loc = latestStatus.value?.location_info ?? latestStatus.value?.location;
    if (!loc) return null;
    try {
      const obj = typeof loc === 'string' ? JSON.parse(loc) : loc;
      if (typeof obj.x === 'number' && typeof obj.y === 'number') {
        return { x: obj.x, y: obj.y, angle: obj.angle ?? 0 };
      }
    } catch {
      /* ignore */
    }
    return null;
  });

  async function loadRobotList() {
    loading.value = true;
    try {
      // 跨模块下拉用 /robot/manage/all（仅需登录，无 robot:manage:list 权限），
      // 避免运营监控页面因缺少机器人管理权限而报「权限不足」
      const { data } = await fetchGetAllRobots();
      if (data) {
        robotList.value = data;
      }
    } catch {
      robotList.value = [];
    } finally {
      loading.value = false;
    }
  }

  async function refreshStatus() {
    if (!selectedRobotId.value) return;
    try {
      const { data } = await fetchGetLatestRobotStatus(selectedRobotId.value);
      if (!data) return;
      latestStatus.value = data as unknown as Api.Robot.RobotStatusRecord;
      // 把 status/latest 返回的实时在线状态同步到机器人列表，
      // 让下拉框、视频监控等依赖 robot.status 的展示实时刷新
      const robot = robotList.value.find(r => r.id === selectedRobotId.value);
      if (robot) {
        robot.status = data.status;
      }
    } catch {
      /* ignore */
    }
  }

  function startPolling() {
    stopPolling();
    pollingTimer = setInterval(refreshStatus, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollingTimer !== null) {
      clearInterval(pollingTimer);
      pollingTimer = null;
    }
  }

  async function selectRobot(id: number) {
    selectedRobotId.value = id;
    latestStatus.value = null;
    await refreshStatus();
    startPolling();
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      stopPolling();
    } else if (selectedRobotId.value) {
      refreshStatus();
      startPolling();
    }
  }

  watch(selectedRobotId, () => {
    if (!selectedRobotId.value) {
      stopPolling();
    }
  });

  onMounted(async () => {
    await loadRobotList();
    const firstOnline = robotList.value.find(r => r.status === 'online');
    const first = firstOnline ?? robotList.value[0];
    if (first) {
      await selectRobot(first.id);
    }
    document.addEventListener('visibilitychange', handleVisibilityChange);
  });

  onBeforeUnmount(() => {
    stopPolling();
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  });

  return {
    robotList,
    selectedRobotId,
    selectedRobot,
    latestStatus,
    parsedLocation,
    loading,
    selectRobot
  };
}
