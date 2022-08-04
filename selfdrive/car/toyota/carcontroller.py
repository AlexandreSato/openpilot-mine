from cereal import car
from common.numpy_fast import clip, interp
from selfdrive.car import apply_toyota_steer_torque_limits, create_gas_command, make_can_msg
from selfdrive.car.toyota.toyotacan import create_steer_command, create_ui_command, \
                                           create_accel_command, create_acc_cancel_command, \
                                           create_fcw_command, create_lta_steer_command
from selfdrive.car.toyota.values import CAR, STATIC_DSU_MSGS, NO_STOP_TIMER_CAR, TSS2_CAR, \
                                        MIN_ACC_SPEED, PEDAL_HYST_GAP, PEDAL_SCALE, CarControllerParams
from opendbc.can.packer import CANPacker
from common.op_params import opParams

VisualAlert = car.CarControl.HUDControl.VisualAlert


def accel_hysteresis(accel, accel_steady, enabled):

  # for small accel oscillations within ACCEL_HYST_GAP, don't change the accel command
  if not enabled:
    # send 0 when disabled, otherwise acc faults
    accel_steady = 0.
  elif accel > accel_steady + CarControllerParams.ACCEL_HYST_GAP:
    accel_steady = accel - CarControllerParams.ACCEL_HYST_GAP
  elif accel < accel_steady - CarControllerParams.ACCEL_HYST_GAP:
    accel_steady = accel + CarControllerParams.ACCEL_HYST_GAP
  accel = accel_steady

  return accel, accel_steady


def coast_accel(speed):  # given a speed, output coasting acceleration
  points = [[0.0, 0.03], [.166, .424], [.335, .568],
            [.731, .440], [1.886, 0.262], [2.809, -0.207],
            [3.443, -0.249], [MIN_ACC_SPEED, -0.145]]
  return interp(speed, *zip(*points))


def compute_gb_pedal(accel, speed):
  _a3, _a4, _a5, _offset, _e1, _e2, _e3, _e4, _e5, _e6, _e7, _e8 = [-0.07264304340456754, -0.007522016704006004, 0.16234124452228196, 0.0029096574419830296, 1.1674372321165579e-05, -0.008010070095545522, -5.834025253616562e-05, 0.04722441060805912, 0.001887454016549489, -0.0014370672920621269, -0.007577594283906699, 0.01943515032956308]
  speed_part = (_e5 * accel + _e6) * speed ** 2 + (_e7 * accel + _e8) * speed
  accel_part = ((_e1 * speed + _e2) * accel ** 5 + (_e3 * speed + _e4) * accel ** 4 + _a3 * accel ** 3 + _a4 * accel ** 2 + _a5 * accel)
  return speed_part + accel_part + _offset



class CarController():
  def __init__(self, dbc_name, CP, VM):
    self.last_steer = 0
    self.accel_steady = 0.
    self.alert_active = False
    self.last_standstill = False
    self.standstill_req = False
    self.steer_rate_limited = False
    self.use_interceptor = False
    self.standstill_hack = opParams().get('standstill_hack')
    # silent disengage
    self.frame = 0
    self.pcm_cancel_frame = float('-inf')
    # self.prev_pcm_cancel = 0

    self.packer = CANPacker(dbc_name)

  def update(self, enabled, CS, frame, actuators, pcm_cancel_cmd, hud_alert,
             left_line, right_line, lead, left_lane_depart, right_lane_depart):

    # *** compute control surfaces ***

    # gas and brake
    interceptor_gas_cmd = 0.
    pcm_accel_cmd = actuators.accel

    if CS.CP.enableGasInterceptor:
      # handle hysteresis when around the minimum acc speed
      if CS.out.vEgo < MIN_ACC_SPEED:
        self.use_interceptor = True
      elif CS.out.vEgo > MIN_ACC_SPEED + PEDAL_HYST_GAP:
        self.use_interceptor = False

      if self.use_interceptor and enabled:
        # only send negative accel when using interceptor. gas handles acceleration
        # +0.18 m/s^2 offset to reduce ABS pump usage when OP is engaged
        if pcm_accel_cmd > coast_accel(CS.out.vEgo):
          interceptor_gas_cmd = clip(compute_gb_pedal(pcm_accel_cmd, CS.out.vEgo), 0., 1.)
        pcm_accel_cmd = 0.18 - max(0, -actuators.accel)

    pcm_accel_cmd, self.accel_steady = accel_hysteresis(pcm_accel_cmd, self.accel_steady, enabled)
    pcm_accel_cmd = clip(pcm_accel_cmd, CarControllerParams.ACCEL_MIN, CarControllerParams.ACCEL_MAX)

    # steer torque
    new_steer = int(round(actuators.steer * CarControllerParams.STEER_MAX))
    apply_steer = apply_toyota_steer_torque_limits(new_steer, self.last_steer, CS.out.steeringTorqueEps, CarControllerParams)
    self.steer_rate_limited = new_steer != apply_steer

    # Cut steering while we're in a known fault state (2s)
    if not enabled or CS.steer_state in [9, 25] or abs(CS.out.steeringRateDeg) > 100:
      apply_steer = 0
      apply_steer_req = 0
    else:
      apply_steer_req = 1

    if not enabled and CS.pcm_acc_status:
      # send pcm acc cancel cmd if drive is disabled but pcm is still on, or if the system can't be activated
      pcm_cancel_cmd = 1

    # silent disengage
    if pcm_cancel_cmd:
      self.pcm_cancel_frame = self.frame

    # on entering standstill, send standstill request
    if CS.out.standstill and not self.last_standstill and CS.CP.carFingerprint not in NO_STOP_TIMER_CAR and not self.standstill_hack:
      self.standstill_req = True
    if CS.pcm_acc_status != 8:
      # pcm entered standstill or it's disabled
      self.standstill_req = False

    self.last_steer = apply_steer
    self.last_accel = pcm_accel_cmd
    self.last_standstill = CS.out.standstill

    can_sends = []

    #*** control msgs ***
    #print("steer {0} {1} {2} {3}".format(apply_steer, min_lim, max_lim, CS.steer_torque_motor)

    # toyota can trace shows this message at 42Hz, with counter adding alternatively 1 and 2;
    # sending it at 100Hz seem to allow a higher rate limit, as the rate limit seems imposed
    # on consecutive messages
    can_sends.append(create_steer_command(self.packer, apply_steer, apply_steer_req, frame))
    if frame % 2 == 0 and CS.CP.carFingerprint in TSS2_CAR:
      can_sends.append(create_lta_steer_command(self.packer, 0, 0, frame // 2))

    # LTA mode. Set ret.steerControlType = car.CarParams.SteerControlType.angle and whitelist 0x191 in the panda
    # if frame % 2 == 0:
    #   can_sends.append(create_steer_command(self.packer, 0, 0, frame // 2))
    #   can_sends.append(create_lta_steer_command(self.packer, actuators.steeringAngleDeg, apply_steer_req, frame // 2))

    # we can spam can to cancel the system even if we are using lat only control
    if (frame % 3 == 0 and CS.CP.openpilotLongitudinalControl) or pcm_cancel_cmd:
      lead = lead or CS.out.vEgo < 12.    # at low speed we always assume the lead is present do ACC can be engaged

      # Lexus IS uses a different cancellation message
      if pcm_cancel_cmd and CS.CP.carFingerprint == CAR.LEXUS_IS:
        can_sends.append(create_acc_cancel_command(self.packer))
      elif CS.CP.openpilotLongitudinalControl:
        can_sends.append(create_accel_command(self.packer, pcm_accel_cmd, pcm_cancel_cmd, self.standstill_req, lead, CS.acc_type, CS.distance_btn, CS.Fast_Speed_Increments))
      else:
        can_sends.append(create_accel_command(self.packer, 0, pcm_cancel_cmd, False, lead, CS.acc_type, CS.distance_btn, CS.Fast_Speed_Increments))

    if frame % 2 == 0 and CS.CP.enableGasInterceptor:
      # send exactly zero if gas cmd is zero. Interceptor will send the max between read value and gas cmd.
      # This prevents unexpected pedal range rescaling
      can_sends.append(create_gas_command(self.packer, interceptor_gas_cmd, frame // 2))

    # ui mesg is at 100Hz but we send asap if:
    # - there is something to display
    # - there is something to stop displaying
    fcw_alert = hud_alert == VisualAlert.fcw
    lda_hold_wheel = hud_alert in [VisualAlert.steerRequired, VisualAlert.ldw]

    send_ui = False
    if ((fcw_alert or lda_hold_wheel) and not self.alert_active) or \
       (not (fcw_alert or lda_hold_wheel) and self.alert_active):
      send_ui = True
      self.alert_active = not self.alert_active
    elif self.frame - self.pcm_cancel_frame < 10:
      # forcing the pcm to disengage causes a bad fault sound so mask with a silent alert
      send_ui = True

    # send additional 5 messages after disengage with silent alert, then 5 with no alert to quickly hide alert
    lda_hold_wheel |= self.frame - self.pcm_cancel_frame < 5
    if (frame % 100 == 0 or send_ui):
      can_sends.append(create_ui_command(self.packer, lda_hold_wheel, left_line, right_line, left_lane_depart, right_lane_depart, enabled))

    if frame % 100 == 0 and CS.CP.enableDsu:
      can_sends.append(create_fcw_command(self.packer, fcw_alert))

    #*** static msgs ***

    for (addr, cars, bus, fr_step, vl) in STATIC_DSU_MSGS:
      if frame % fr_step == 0 and CS.CP.enableDsu and CS.CP.carFingerprint in cars:
        can_sends.append(make_can_msg(addr, vl, bus))

    # silent disengage
    self.frame += 1

    return can_sends
