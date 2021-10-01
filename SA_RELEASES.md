Stock Additions Update 2 - 2021-08-15 (0.8.9)
===
 * Update SA to 0.8.9 with new model from upstream!
 * Experimental model cruise control button is back

Stock Additions Update 1 - 2021-08-15 (0.8.7)
===
 * Update SA to 0.8.7!
 * Variable longitudinal lag by speed
 * Toyota: add ML-based steering controller enabled by parameter `use_steering_model`

Stock Additions Update 3 - 2021-05-03 (0.8.2)
===
 * Remove eager accel and instead send future desired accel
   * Much simpler and better/smoother results (tunable with `long_accel_delay`)

Stock Additions Update 2 - 2021-04-21 (0.8.2)
===
 * Update versioning sceme to *Updates*, which reset on each new openpilot version
 * For pedal users: convert acceleration to correct gas percentage for smooth gas control (dynamic gas isn't needed anymore!)
 * Offroad apk with color correction option from ihsakashi
 * opParams and opEdit: Make more params live! Any param not marked `static` can be adjusted while onroad! The non-static non-live params update within 10 seconds.
 * New param to change at which speed lane changes become nudgeless above (`alca_no_nudge_speed`)
 * Experimental feature: eager acceleration (read the README under general features)
 * More accurate LDW warning
 * Features ported from 0.8.3:
   * The newest KL model, and a param to enable laneless
   * (0.8.4) The laneless MPC retune fix from Harald
   * A few car firmware updates
   * GPS malfunction fix

Stock Additions v0.6.6 - 2021-02-27 (0.8.2)
===
 * Continued grey panda support (white panda not guaranteed)
 * Temporary removal of LaneSpeed and DynamicCameraOffset features
   * They used the now-removed lane line polys
 * Remove slowdown_for_curves param
 * Roadtrip profile is now stock longitudinal for smoother road trips
   * No dynamic follow distance modiciations, all stock
 * Add color corrections button, PR by ihsakashi
 * More parameters now update while driving.
   * If the param isn't marked with "static" you no longer have to reboot
 * Parameter `alca_no_nudge_speed` controls the speed at which lane changes go from needing a nudge to "nudgeless"

Stock Additions v0.6.5 - 2020-12-07 (0.8)
===
 * Continued grey panda support (white panda not guaranteed)
 * Raise max limit of global_df_mod to 2.5x
 * Dynamic follow uses an ID controller for distance mods
 * Smoother lat derivative (over 0.05 second interval instead of 0.01)
 * Tune 17 Corolla gas curve
 * TSS2 gas tuning for RAV4 and Prius
 * Param `disengage_on_gas` is False by default
 * Detect if on OneUI 3.0 hotspot (different IP addresses)
 * Made ML button smaller
 * Speed turns red while braking

Stock Additions v0.6 - 2020-11-09 (0.7.10)
===
 * Update Stock Additions to openpilot v0.7.10
 * Smoother dynamic follow with less complexity (experimental)
 * Raise max limit of global_df_mod to 1.5x
 * Continued white panda support (untested, grey gives no warning)
 * Reduced DM uncertain alert at night with EON
 * Add slow down for curves from openpilot 0.6.3 (by parameter toggle `slowdown_for_curves`)

Stock Additions v0.5.4 - 2020-10-15 (0.7.7)
===
 * Make model path default grey when not engaged, only color when engaged
 * About 1.6 seconds faster starting up (from a recent commit from stock)
 * Colorful loading spinner: RGB!
 * Revert back to original release2 driving model

Stock Additions v0.5.3 - 2020-9-15 (0.7.7)
===
 * Properly set unsafe_mode in boardd. This might fix panda flashing issues for new users, since it won't be required
 * Separate 2020 Prius and add PID tune
 * Support 2021 TSS2 Prius
 * Add param `standstill_hack` for stop and go hack
 * Add param `update_behavior` to change how SA updates. off never updates, auto reboots if there's an update, and alert shows a button offroad with changelog
 * Retune TSS1 Corolla for better curve handling
 * Tune TSS2 Corolla (INDI, thanks to birdman6450)

Stock Additions v0.5.2 - 2020-9-11 (0.7.7)
===
 * Fix jerking after dynamic camera offset is complete, it now smoothly ramps back to center

Stock Additions v0.5.1 - 2020-9-10 (0.7.7)
===
 * Disable automatic updates by default and show changelog in apk (you can enable the param auto_update to revert this)

Stock Additions v0.5 - 2020-9-10 (0.7.7)
===
 * LaneSpeed process is much more efficient, CPU usage down from 6% (causing lag alerts) to ~1%
   * Use numpy_fast.interp instead of np.interp for slight boost in performance
 * Support white panda with experimental parameter. localizer performance may be reduced
 * Fixed silent alerts due to the new alert manager in 0.7.7
 * Make all the UI buttons show their state with unique colors!
   * Also added more colors to opEdit!
 * Add derivative to lateral PI control for TSS1 & TSS2 Corolla and Prius!
 * Add a Reset to origin button to TextWindow when an error occurs
 * Color coded model lane lines and path
 * Add ZSS support

Stock Additions v0.4 - 2020-7-18 (0.7.5)
===
 * Various opEdit improvements, colors, highlighting of last explored param, quicker messages
 * New Dynamic Follow modification to help slow and accelerate sooner
 * Live parameters update quicker
 * dfManager reliability improvements
 * New LaneSpeed and Dynamic Camera Offset features added

Stock Additions v0.3 - 2020-5-13 (0.7.4)
===
 * Sidebar will not pop out when you tap the Dynamic Follow profile change button when driving
 * Add derivative to longcontrol. Improves responsiveness and helps overshoot

Stock Additions v0.2 - 2020-3-15 (0.7.1)
===
 * Recover faster when lead leaves path, or when braking or acceleration is required immediately. Also should speed up the acceleration with auto lane change.
 * Add 3 different dynamic follow profiles: `roadtrip`, `relaxed`, and `traffic`. `relaxed` is the current dynamic follow profile. You can also swap profiles without rebooting live by using opEdit. SSH in and: `cd /data/openpilot;python op_edit.py` The parameter to change is `dynamic_follow`
 * Fix for steering unavailable when wheel goes over 100 degrees/sec.
 * Tuning for dynamic gas
 * Accelerate quicker and get closer when you're lane changing
 * Higher acceleration, and higher limits for turns
 * Automatic updates, EON will reboot by itself as long as it is inactive

Stock Additions v0.1 - 2020-1-14 (0.7)
===
 * Dynamic lane speed is a new feature that reduces your cruising speed if many vehicles around you are significantly slower than you. This works with and without an openpilot-identified lead.
 * Dynamic gas tuning. Above 20 mph we take lead velocity and the following distance into account. Possibility of different tuning for different cars in the future. (DYNAMIC GAS NOW ONLY WORKS ON TOYOTA COROLLA AND RAV4 PEDAL)
 * Dynamic follow tuning, don't get as close when lead is accelerating.
 * Added static_steer_ratio parameter, if True openpilot will use the steer ratio in your interface file. Default is true, false uses the openpilot learned value which can vary through your drives.
 * Added ability to live tune parameters with `op_tune.py`. Currently only the camera offset (`camera_offset`) is supported.
 * Some Corolla tuning.
 * Reduce max acceleration.
 * TO NOTE: Dynamic Lane Speed will not work with stopped cars, at any speed. There is also a margin that cars must be traveling within in order to affect your speed. Don't expect anything magical, just minor quality of drive improvements.
