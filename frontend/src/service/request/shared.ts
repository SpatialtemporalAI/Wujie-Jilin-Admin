import { useAuthStore } from '@/store/modules/auth';
import { localStg } from '@/utils/storage';
import { fetchRefreshToken } from '../api';
import type { RequestInstanceState } from './type';

export function getAuthorization() {
  const token = localStg.get('token');
  const Authorization = token ? `${token}` : null;

  return Authorization;
}

/** refresh token */
async function handleRefreshToken() {
  const { resetStore } = useAuthStore();

  const rToken = localStg.get('refreshToken') || '';
  const { error, data } = await fetchRefreshToken(rToken);
  if (!error) {
    const tokenWithType = `${data.token_type} ${data.access_token}`;
    localStg.set('token', tokenWithType);
    localStg.set('refreshToken', data.refresh_token);
    return true;
  }

  resetStore();

  return false;
}

export async function handleExpiredRequest(state: RequestInstanceState) {
  if (!state.refreshTokenPromise) {
    state.refreshTokenPromise = handleRefreshToken();
  }

  const success = await state.refreshTokenPromise;

  setTimeout(() => {
    state.refreshTokenPromise = null;
  }, 1000);

  return success;
}

export function showErrorMsg(state: RequestInstanceState, message: string) {
  if (!message) return;

  if (!state.errMsgStack?.length) {
    state.errMsgStack = [];
  }

  const isExist = state.errMsgStack.includes(message);

  if (isExist) return;

  state.errMsgStack.push(message);

  const onLeave = () => {
    state.errMsgStack = state.errMsgStack.filter(msg => msg !== message);
    setTimeout(() => {
      state.errMsgStack = [];
    }, 5000);
  };

  if (window.$message?.error) {
    window.$message.error(message, { onLeave });
    return;
  }

  // Fallback：$message 尚未挂载时（如登录页首次加载即触发请求），轮询一段时间再弹
  let tries = 0;
  const timer = setInterval(() => {
    tries += 1;
    if (window.$message?.error) {
      clearInterval(timer);
      window.$message.error(message, { onLeave });
    } else if (tries >= 20) {
      clearInterval(timer);
      onLeave();
      // 最后兜底：alert，确保用户能看到
      // eslint-disable-next-line no-alert
      window.alert(message);
    }
  }, 100);
}
