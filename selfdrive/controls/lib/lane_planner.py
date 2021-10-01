from common.numpy_fast import interp, clip
import numpy as np
from cereal import log
from common.filter_simple import FirstOrderFilter
from common.numpy_fast import interp
from common.realtime import DT_MDL
from selfdrive.hardware import EON, TICI
from selfdrive.swaglog import cloudlog
from common.op_params import opParams


TRAJECTORY_SIZE = 33
# camera offset is meters from center car to camera
if EON:
  STANDARD_CAMERA_OFFSET = 0.06  # do NOT change this. edit with opEdit
  STANDARD_PATH_OFFSET = 0.0  # do NOT change this. edit with opEdit
  # CAMERA_OFFSET = 0.06
  # PATH_OFFSET = 0.0
elif TICI:
  STANDARD_CAMERA_OFFSET = -0.04  # do NOT change this. edit with opEdit
  STANDARD_PATH_OFFSET = -0.04  # do NOT change this. edit with opEdit
  # CAMERA_OFFSET = -0.04
  # PATH_OFFSET = -0.04
else:
  STANDARD_CAMERA_OFFSET = 0.0  # do NOT change this. edit with opEdit
  STANDARD_PATH_OFFSET = 0.0  # do NOT change this. edit with opEdit
  # CAMERA_OFFSET = 0.0
  # PATH_OFFSET = 0.0


class LanePlanner:
  def __init__(self, wide_camera=False):
    self.ll_t = np.zeros((TRAJECTORY_SIZE,))
    self.ll_x = np.zeros((TRAJECTORY_SIZE,))
    self.lll_y = np.zeros((TRAJECTORY_SIZE,))
    self.rll_y = np.zeros((TRAJECTORY_SIZE,))
    self.lane_width_estimate = FirstOrderFilter(3.7, 9.95, DT_MDL)
    self.lane_width_certainty = FirstOrderFilter(1.0, 0.95, DT_MDL)
    self.lane_width = 3.7
    self.op_params = opParams()
    # self.camera_offset = self.op_params.get('camera_offset')

    self.lll_prob = 0.
    self.rll_prob = 0.
    self.d_prob = 0.

    self.lll_std = 0.
    self.rll_std = 0.

    self.l_lane_change_prob = 0.
    self.r_lane_change_prob = 0.

    # self.camera_offset = -STANDARD_CAMERA_OFFSET if wide_camera else STANDARD_CAMERA_OFFSET
    if TICI:
      self.path_offset = -STANDARD_PATH_OFFSET if wide_camera else STANDARD_PATH_OFFSET

  def parse_model(self, md):
    if len(md.laneLines) == 4 and len(md.laneLines[0].t) == TRAJECTORY_SIZE:
      self.camera_offset = clip(self.op_params.get('camera_offset'), -0.3, 0.3)  # update camera offset
      if not TICI:  # TODO: make sure this is correct
        self.path_offset = self.camera_offset - STANDARD_CAMERA_OFFSET + STANDARD_PATH_OFFSET  # offset path

      self.ll_t = (np.array(md.laneLines[1].t) + np.array(md.laneLines[2].t))/2
      # left and right ll x is the same
      self.ll_x = md.laneLines[1].x
      # only offset left and right lane lines; offsetting path does not make sense
      self.lll_y = np.array(md.laneLines[1].y) - self.camera_offset
      self.rll_y = np.array(md.laneLines[2].y) - self.camera_offset
      self.lll_prob = md.laneLineProbs[1]
      self.rll_prob = md.laneLineProbs[2]
      self.lll_std = md.laneLineStds[1]
      self.rll_std = md.laneLineStds[2]

    if len(md.meta.desireState):
      self.l_lane_change_prob = md.meta.desireState[log.LateralPlan.Desire.laneChangeLeft]
      self.r_lane_change_prob = md.meta.desireState[log.LateralPlan.Desire.laneChangeRight]

  def get_d_path(self, v_ego, path_t, path_xyz):
    # Reduce reliance on lanelines that are too far apart or
    # will be in a few seconds
    path_xyz[:, 1] -= self.path_offset
    l_prob, r_prob = self.lll_prob, self.rll_prob
    width_pts = self.rll_y - self.lll_y
    prob_mods = []
    for t_check in [0.0, 1.5, 3.0]:
      width_at_t = interp(t_check * (v_ego + 7), self.ll_x, width_pts)
      prob_mods.append(interp(width_at_t, [4.0, 5.0], [1.0, 0.0]))
    mod = min(prob_mods)
    l_prob *= mod
    r_prob *= mod

    # Reduce reliance on uncertain lanelines
    l_std_mod = interp(self.lll_std, [.15, .3], [1.0, 0.0])
    r_std_mod = interp(self.rll_std, [.15, .3], [1.0, 0.0])
    l_prob *= l_std_mod
    r_prob *= r_std_mod

    # Find current lanewidth
    self.lane_width_certainty.update(l_prob * r_prob)
    current_lane_width = abs(self.rll_y[0] - self.lll_y[0])
    self.lane_width_estimate.update(current_lane_width)
    speed_lane_width = interp(v_ego, [0., 31.], [2.8, 3.5])
    self.lane_width = self.lane_width_certainty.x * self.lane_width_estimate.x + \
                      (1 - self.lane_width_certainty.x) * speed_lane_width

    clipped_lane_width = min(4.0, self.lane_width)
    path_from_left_lane = self.lll_y + clipped_lane_width / 2.0
    path_from_right_lane = self.rll_y - clipped_lane_width / 2.0

    self.d_prob = l_prob + r_prob - l_prob * r_prob
    lane_path_y = (l_prob * path_from_left_lane + r_prob * path_from_right_lane) / (l_prob + r_prob + 0.0001)
    safe_idxs = np.isfinite(self.ll_t)
    if safe_idxs[0]:
      lane_path_y_interp = np.interp(path_t, self.ll_t[safe_idxs], lane_path_y[safe_idxs])
      path_xyz[:,1] = self.d_prob * lane_path_y_interp + (1.0 - self.d_prob) * path_xyz[:,1]
    else:
      cloudlog.warning("Lateral mpc - NaNs in laneline times, ignoring")
    return path_xyz
