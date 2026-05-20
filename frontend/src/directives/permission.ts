import type { Directive, DirectiveBinding } from 'vue';
import { useAuth } from '@/hooks/business/auth';

export const permission: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const { hasAuth } = useAuth();
    const value = binding.value;

    if (!value) return;

    const codes = typeof value === 'string' ? [value] : value;
    const hasPermission = hasAuth(codes);

    if (!hasPermission) {
      el.parentNode?.removeChild(el);
    }
  }
};
