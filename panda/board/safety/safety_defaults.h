const addr_checks default_rx_checks = {
  .check = NULL,
  .len = 0,
};

int default_rx_hook(CAN_FIFOMailBox_TypeDef *to_push) {
  UNUSED(to_push);
  return true;
}

// **** this for send acc_type1 ****
int block = 0;
uint32_t eon_detected_last = 0;
void send_acctype1(void);
uint32_t startedtime = 0;
bool onboot = 0;
bool boot_done = 0;


// *** no output safety mode ***

static const addr_checks* nooutput_init(int16_t param) {
  UNUSED(param);
  controls_allowed = false;
  relay_malfunction_reset();
  return &default_rx_checks;
}

static int nooutput_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  UNUSED(to_send);
  return false;
}

static int nooutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return false;
}

static int default_fwd_hook(int bus_num, CAN_FIFOMailBox_TypeDef *to_fwd) {
  // UNUSED(bus_num);
  // UNUSED(to_fwd);
  int bus_fwd = -1;
  int addr = GET_ADDR(to_fwd);
  if(bus_num == 0){
    // create a timer and measure elapsed time
    uint32_t ts = TIM2->CNT;
    uint32_t ts_elapsed = get_ts_elapsed(ts, eon_detected_last);
    // reset blocking flag if time since we saw the Eon exceeds limit
    if (ts_elapsed > 250000) {
      block = 0;
    }
    // do we see the Eon?
    if(addr == 0x343){
      block = 1;
      eon_detected_last = ts;
    }
    bus_fwd = 2;
  }
  if(bus_num == 2){
    // block cruise message only if it's already being sent on bus 0
    if(!onboot){
      startedtime = TIM2->CNT;
      onboot = 1;
    }
    // spam the acc_type1 msg for 2sec
    boot_done = (TIM2->CNT > (startedtime + 2000000));
    if (!boot_done){
      send_acctype1();
    }
    int blockmsg = (block | !boot_done) && (addr == 0x343);
    if(!blockmsg){ 
      bus_fwd = 0;
    }
  }
  return bus_fwd;
}

const safety_hooks nooutput_hooks = {
  .init = nooutput_init,
  .rx = default_rx_hook,
  .tx = nooutput_tx_hook,
  .tx_lin = nooutput_tx_lin_hook,
  .fwd = default_fwd_hook,
};

// *** all output safety mode ***

static const addr_checks* alloutput_init(int16_t param) {
  UNUSED(param);
  controls_allowed = true;
  relay_malfunction_reset();
  return &default_rx_checks;
}

static int alloutput_tx_hook(CAN_FIFOMailBox_TypeDef *to_send) {
  UNUSED(to_send);
  return true;
}

static int alloutput_tx_lin_hook(int lin_num, uint8_t *data, int len) {
  UNUSED(lin_num);
  UNUSED(data);
  UNUSED(len);
  return true;
}

const safety_hooks alloutput_hooks = {
  .init = alloutput_init,
  .rx = default_rx_hook,
  .tx = alloutput_tx_hook,
  .tx_lin = alloutput_tx_lin_hook,
  .fwd = default_fwd_hook,
};
