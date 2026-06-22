import { useAuthStore } from '@/store/modules/auth';

export function useAuth() {
  const authStore = useAuthStore();

  function hasAuth(codes: string | string[]) {
    if (!authStore.isLogin) {
      return false;
    }
    const buttons = authStore.userInfo.buttons
    console.log('robot:manage:add 在 buttons 里?', buttons.includes('robot:manage:add'));
    console.log('robot:manage:delete 在 buttons 里?', buttons.includes('robot:manage:delete'));
    console.log('完整 buttons:', JSON.stringify(buttons));
    if (typeof codes === 'string') {
      return authStore.userInfo.buttons.includes(codes);
    }

    return codes.some(code => authStore.userInfo.buttons.includes(code));
  }

  return {
    hasAuth
  };
}
