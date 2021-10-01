// unittest for set_exposure_target

#include "ae_gray_test.h"

#include <cassert>

#include <cmath>
#include <cstring>

#include "selfdrive/common/util.h"
#include "selfdrive/camerad/cameras/camera_common.h"

// needed by camera_common.cc
ExitHandler do_exit;

void camera_autoexposure(CameraState *s, float grey_frac) {}

int main() {
  // set up fake camerabuf
  CameraBuf cb = {};
  VisionBuf vb = {};
  uint8_t * fb_y = new uint8_t[W*H];
  vb.y = fb_y;
  cb.cur_yuv_buf = &vb;
  cb.rgb_width = W;
  cb.rgb_height = H;

  printf("AE test patterns %dx%d\n", cb.rgb_width, cb.rgb_height);

  // mix of 5 tones
  uint8_t l[5] = {0, 24, 48, 96, 235}; // 235 is yuv max

  bool passed = true;
  float rtol = 0.05;
  // generate pattern and calculate EV
  int cnt = 0;
  for (int i_0=0; i_0<TONE_SPLITS; i_0++) {
    for (int i_1=0; i_1<TONE_SPLITS; i_1++) {
      for (int i_2=0; i_2<TONE_SPLITS; i_2++) {
        for (int i_3=0; i_3<TONE_SPLITS; i_3++) {
          int h_0 = i_0 * H / TONE_SPLITS;
          int h_1 = i_1 * (H - h_0) / TONE_SPLITS;
          int h_2 = i_2 * (H - h_0 - h_1) / TONE_SPLITS;
          int h_3 = i_3 * (H - h_0 - h_1 - h_2) / TONE_SPLITS;
          int h_4 = H - h_0 - h_1 - h_2 - h_3;
          memset(&fb_y[0], l[0], h_0*W);
          memset(&fb_y[h_0*W], l[1], h_1*W);
          memset(&fb_y[h_0*W+h_1*W], l[2], h_2*W);
          memset(&fb_y[h_0*W+h_1*W+h_2*W], l[3], h_3*W);
          memset(&fb_y[h_0*W+h_1*W+h_2*W+h_3*W], l[4], h_4*W);
          float ev = set_exposure_target((const CameraBuf*) &cb, 0, W-1, 1, 0, H-1, 1);
          // printf("%d/%d/%d/%d/%d ev is %f\n", h_0, h_1, h_2, h_3, h_4, ev);
          // printf("%f\n", ev);

          // compare to gt
          float evgt = gts[cnt];
          if (fabs(ev - evgt) > rtol*evgt) {
            passed = false;
          }

          // report
          printf("%d/%d/%d/%d/%d: ev %f, gt %f, err %f\n", h_0, h_1, h_2, h_3, h_4, ev, evgt, fabs(ev - evgt) / (evgt != 0 ? evgt : 0.00001f));
          cnt++;
        }
      }
    }
  }
  assert(passed);

  delete[] fb_y;
  return 0;
}
