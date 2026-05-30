import { ref, shallowRef } from 'vue';
import { fetchGetCaptcha, fetchVerifyCaptcha } from '@/service/api/auth';

export function useSliderCaptcha() {
  const captchaRequired = ref(false);
  const captchaToken = ref<string | null>(null);

  const captchaId = ref('');
  const backgroundImage = ref('');
  const puzzleImage = ref('');
  const puzzleY = ref(0);
  const sliderWidth = ref(350);
  const loading = ref(false);

  async function fetchCaptcha() {
    loading.value = true;
    try {
      const { data, error } = await fetchGetCaptcha();
      if (!error && data) {
        captchaId.value = data.captcha_id;
        backgroundImage.value = data.background_image;
        puzzleImage.value = data.puzzle_image;
        puzzleY.value = data.puzzle_y;
        sliderWidth.value = data.slider_width;
      }
    } finally {
      loading.value = false;
    }
  }

  async function verifyCaptcha(slideX: number): Promise<boolean> {
    const { data, error } = await fetchVerifyCaptcha(captchaId.value, slideX);
    if (!error && data) {
      captchaToken.value = data.captcha_token;
      return true;
    }
    return false;
  }

  function showCaptcha() {
    captchaRequired.value = true;
    captchaToken.value = null;
    fetchCaptcha();
  }

  function resetCaptcha() {
    captchaRequired.value = false;
    captchaToken.value = null;
    captchaId.value = '';
    backgroundImage.value = '';
    puzzleImage.value = '';
  }

  return {
    captchaRequired,
    captchaToken,
    captchaId,
    backgroundImage,
    puzzleImage,
    puzzleY,
    sliderWidth,
    loading,
    fetchCaptcha,
    verifyCaptcha,
    showCaptcha,
    resetCaptcha
  };
}
