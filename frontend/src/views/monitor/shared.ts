import { onBeforeUnmount, onMounted, ref } from 'vue';
import { fetchGetApiStats, fetchGetSystemMetrics } from '@/service/api/monitor';

export function useMonitorData() {
  const systemMetrics = ref<Api.Monitor.SystemMetrics | null>(null);
  const apiStats = ref<Api.Monitor.ApiStats[]>([]);
  const loading = ref(false);
  let timer: ReturnType<typeof setInterval> | null = null;

  async function refresh() {
    loading.value = true;
    try {
      const [{ data: metrics }, { data: stats }] = await Promise.all([
        fetchGetSystemMetrics(),
        fetchGetApiStats({ minutes: 60 })
      ]);
      if (metrics) {
        systemMetrics.value = metrics;
      }
      if (stats) {
        apiStats.value = stats;
      }
    } finally {
      loading.value = false;
    }
  }

  function startPolling(interval = 5000) {
    refresh();
    timer = setInterval(refresh, interval);
  }

  function stopPolling() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  onMounted(() => {
    startPolling();
  });

  onBeforeUnmount(() => {
    stopPolling();
  });

  return {
    systemMetrics,
    apiStats,
    loading,
    refresh
  };
}
