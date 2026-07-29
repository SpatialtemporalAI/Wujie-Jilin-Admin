import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { type RemoteTrackPublication, Room, RoomEvent, Track } from 'livekit-client';
import { fetchCloseVideoMonitoring, fetchOpenVideoMonitoring, fetchVideoMonitoringHeartbeat } from '@/service/api';

const HEARTBEAT_INTERVAL = 15000;

export interface UseLiveKitVideoOptions {
  robotId: number;
  serialNumber: string;
  status: Api.Robot.RobotStatusEnum;
}

export function useLiveKitVideo(options: UseLiveKitVideoOptions) {
  const videoRef = ref<HTMLVideoElement | null>(null);
  const loading = ref(false);
  const connected = ref(false);
  const error = ref<string | null>(null);
  // 视频轨实时指标，供监控界面展示
  const resolution = ref('');
  const frameRate = ref('');

  let room: Room | null = null;
  // 当前已连接会话的机器人 ID / 观众 ID，切换机器人时用于正确关闭旧视频
  let sessionRobotId: number | null = null;
  let sessionViewerId: string | null = null;
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  let pendingHeartbeat: Promise<void> | null = null;
  // 当前已附加的视频轨，用于读取分辨率/帧率
  let currentTrack: Track | null = null;
  let metricsTimer: ReturnType<typeof setInterval> | null = null;

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  async function waitPendingHeartbeat() {
    if (pendingHeartbeat) {
      try {
        await pendingHeartbeat;
      } catch {
        // 忽略心跳本身的错误，避免关闭时弹出过期提示
      }
      pendingHeartbeat = null;
    }
  }

  function startHeartbeat() {
    stopHeartbeat();
    const robotId = sessionRobotId;
    const viewerId = sessionViewerId;
    if (!robotId || !viewerId) return;
    heartbeatTimer = setInterval(async () => {
      if (pendingHeartbeat) return;
      pendingHeartbeat = fetchVideoMonitoringHeartbeat(robotId, viewerId)
        .then(() => {
          pendingHeartbeat = null;
        })
        .catch(err => {
          pendingHeartbeat = null;
          console.error('视频监控心跳失败', err);
        });
    }, HEARTBEAT_INTERVAL);
  }

  function resetSession() {
    sessionRobotId = null;
    sessionViewerId = null;
  }

  function readTrackMetrics() {
    if (!currentTrack) return;
    try {
      const settings = currentTrack.mediaStreamTrack?.getSettings?.() || {};
      if (settings.width && settings.height) {
        resolution.value = `${settings.width}×${settings.height}`;
      }
      if (settings.frameRate) {
        frameRate.value = `${Math.round(settings.frameRate)}`;
      }
    } catch {
      // 读取失败时保留上次值
    }
  }

  function startMetricsPolling() {
    stopMetricsPolling();
    // 自适应流（adaptiveStream）会动态调整分辨率，定时读取以反映变化
    metricsTimer = setInterval(readTrackMetrics, 1000);
  }

  function stopMetricsPolling() {
    if (metricsTimer) {
      clearInterval(metricsTimer);
      metricsTimer = null;
    }
  }

  function resetMetrics() {
    stopMetricsPolling();
    currentTrack = null;
    resolution.value = '';
    frameRate.value = '';
  }

  async function attachVideoTrack(publication: RemoteTrackPublication) {
    const track = publication.track;
    if (!track || !videoRef.value) return;

    track.attach(videoRef.value);
    currentTrack = track;
    readTrackMetrics();
    startMetricsPolling();
    connected.value = true;
    loading.value = false;
  }

  async function connect() {
    if (!options.robotId || !options.serialNumber) {
      error.value = '未选择机器人';
      return;
    }

    if (options.status !== 'online') {
      await disconnect();
      loading.value = false;
      connected.value = false;
      error.value = null;
      return;
    }

    // 如果已经连接，先断开，确保同一时刻只有一个会话
    await disconnect();

    const expectedRobotId = options.robotId;

    loading.value = true;
    error.value = null;
    connected.value = false;

    try {
      const { data: ticket, error: openErr } = await fetchOpenVideoMonitoring(expectedRobotId);
      if (openErr || !ticket) {
        throw new Error('打开视频监控失败');
      }

      sessionRobotId = expectedRobotId;
      sessionViewerId = ticket.viewer_id;

      // 打开期间如果机器人已切换，关闭刚创建的票据，避免遗留观众
      if (options.robotId !== expectedRobotId) {
        await fetchCloseVideoMonitoring(sessionRobotId, sessionViewerId).catch(() => {});
        resetSession();
        loading.value = false;
        return;
      }

      room = new Room({
        adaptiveStream: true,
        dynacast: true
      });

      room.on(RoomEvent.TrackSubscribed, (_track, publication) => {
        if (publication.kind === Track.Kind.Video) {
          attachVideoTrack(publication);
        }
      });

      room.on(RoomEvent.TrackUnpublished, () => {
        connected.value = false;
        resetMetrics();
      });

      room.on(RoomEvent.Disconnected, reason => {
        connected.value = false;
        resetMetrics();
        console.warn('LiveKit 已断开连接', reason);
      });

      room.on(RoomEvent.ConnectionStateChanged, state => {
        console.log('LiveKit 连接状态变化', state);
      });

      await room.connect(ticket.server_url, ticket.token);
      console.log('LiveKit 连接成功', ticket.room, ticket.viewer_id);
      startHeartbeat();
    } catch (err) {
      loading.value = false;
      connected.value = false;
      error.value = err instanceof Error ? err.message : '视频连接失败';
      console.error('LiveKit 连接失败', err);
    }
  }

  async function disconnect() {
    stopHeartbeat();
    resetMetrics();
    await waitPendingHeartbeat();

    if (room) {
      try {
        room.disconnect();
      } catch (err) {
        console.error('断开 LiveKit room 失败', err);
      } finally {
        room = null;
      }
    }

    const robotId = sessionRobotId;
    const viewerId = sessionViewerId;
    resetSession();

    if (robotId && viewerId) {
      try {
        await fetchCloseVideoMonitoring(robotId, viewerId);
      } catch (err) {
        console.error('关闭视频监控失败', err);
      }
    }
  }

  onMounted(() => {
    connect();
  });

  onBeforeUnmount(() => {
    disconnect();
  });

  // robotId/serialNumber/status 变化时重新处理：
  // - 机器人/序列号变化：在线则重新连接，离线则断开
  // - 状态变化：离线→在线则连接，在线→离线则断开
  // - 避免状态轮询导致无意义的重复连接
  watch(
    () => [options.robotId, options.serialNumber, options.status] as const,
    (newVal, oldVal) => {
      const [newRobotId, newSerial, newStatus] = newVal;
      const [oldRobotId, oldSerial, oldStatus] = oldVal ?? [null, null, null];

      const robotChanged = newRobotId !== oldRobotId || newSerial !== oldSerial;
      const statusChanged = newStatus !== oldStatus;

      if (!robotChanged && !statusChanged) return;

      if (newStatus !== 'online') {
        disconnect();
        return;
      }

      connect();
    }
  );

  return {
    videoRef,
    loading,
    connected,
    error,
    resolution,
    frameRate,
    connect,
    disconnect
  };
}
