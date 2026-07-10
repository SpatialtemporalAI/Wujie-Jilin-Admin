import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
import {
  Room,
  RoomEvent,
  Track,
  type RemoteTrackPublication
} from 'livekit-client';
import {
  fetchOpenVideoMonitoring,
  fetchCloseVideoMonitoring,
  fetchVideoMonitoringHeartbeat
} from '@/service/api';

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

  let room: Room | null = null;
  let viewerId: string | null = null;
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }
  }

  function startHeartbeat(robotId: number, vid: string) {
    stopHeartbeat();
    heartbeatTimer = setInterval(async () => {
      try {
        await fetchVideoMonitoringHeartbeat(robotId, vid);
      } catch (err) {
        console.error('视频监控心跳失败', err);
      }
    }, HEARTBEAT_INTERVAL);
  }

  async function attachVideoTrack(publication: RemoteTrackPublication) {
    const track = publication.track;
    if (!track || !videoRef.value) return;

    track.attach(videoRef.value);
    connected.value = true;
    loading.value = false;
  }

  async function connect() {
    if (!options.robotId || !options.serialNumber) {
      error.value = '未选择机器人';
      return;
    }

    if (options.status !== 'online') {
      loading.value = false;
      connected.value = false;
      error.value = null;
      return;
    }

    // 如果已经连接，先断开
    await disconnect();

    loading.value = true;
    error.value = null;
    connected.value = false;

    try {
      const { data: ticket } = await fetchOpenVideoMonitoring(options.robotId);
      if (!ticket) {
        throw new Error('打开视频监控失败');
      }

      viewerId = ticket.viewer_id;

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
      });

      room.on(RoomEvent.Disconnected, () => {
        connected.value = false;
      });

      await room.connect(ticket.server_url, ticket.token);
      startHeartbeat(options.robotId, ticket.viewer_id);
    } catch (err) {
      loading.value = false;
      connected.value = false;
      error.value = err instanceof Error ? err.message : '视频连接失败';
      console.error('LiveKit 连接失败', err);
    }
  }

  async function disconnect() {
    stopHeartbeat();

    if (room) {
      try {
        room.disconnect();
      } catch (err) {
        console.error('断开 LiveKit room 失败', err);
      } finally {
        room = null;
      }
    }

    if (viewerId && options.robotId) {
      try {
        await fetchCloseVideoMonitoring(options.robotId, viewerId);
      } catch (err) {
        console.error('关闭视频监控失败', err);
      } finally {
        viewerId = null;
      }
    }
  }

  onMounted(() => {
    connect();
  });

  onBeforeUnmount(() => {
    disconnect();
  });

  // robotId/serialNumber/status 变化时重新处理：离线则断开，在线则重新连接
  watch(
    () => [options.robotId, options.serialNumber, options.status],
    () => {
      if (options.status !== 'online') {
        disconnect();
        loading.value = false;
        connected.value = false;
        error.value = null;
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
    connect,
    disconnect
  };
}
