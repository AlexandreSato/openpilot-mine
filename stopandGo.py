#!/usr/bin/env python3
import sys
import os
from panda import Panda
from opendbc.can.packer import CANPacker


max = 500 # increase this if u need more time to start car engine
dbc_name ='toyota_nodsu_hybrid_pt_generated' # put you correct odbc here (search in values.py)

p = Panda()
p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)

dumpsafety = p.health()
if dumpsafety['safety_mode'] == 0:
  print('Sorry, u need change for some dev branch, if u deserv this copy and past this command:\n\n\ncd ..; rm -rf openpilot; git clone -b master --recurse-submodules https://github.com/commaai/openpilot; reboot')
  exit(1)

packer = CANPacker(dbc_name)
values = {
  "ACC_TYPE": 1,
}
data = packer.make_can_msg("ACC_CONTROL", 0, values) # maybe u need change this ACC_CONTROL confirm in your odbc

def main():

  for i in range (0, max):
    print(f"PCM exploit :{data}")
    print(' __      __                                  .___\n/  \    /  \ ____     ____   ____   ____   __| _/\n\   \/\/   // __ \   /    \_/ __ \_/ __ \ / __ | \n \        /\  ___/  |   |  \  ___/\  ___// /_/ | \n  \__/\  /  \___  > |___|  /\___  >\___  >____ | \n       \/       \/       \/     \/     \/     \/ \n  _________        ________ \n /   _____/ ____  /  _____/ \n \_____  \ /    \/   \  ___ \n /        \   |  \    \_\  \\\n/_______  /___|  /\______  /\n        \/     \/        \/ \n')
    p.can_send(data[0], data[2], data[3])
    progress(i, max, 'start your engine before reach the end')
    if i < (max  - 1) :
      os.system('clear')
  
  p.set_safety_mode(Panda.SAFETY_TOYOTA)
  p.send_heartbeat()
  print('\n\n\nrelay ON again\nkthxbay\n')


def progress(count, total, status=''):
  bar_len = 50
  filled_len = int(round(bar_len * count / float(total)))

  bar = '#' * filled_len + '.' * (bar_len - filled_len)

  sys.stdout.write('count :%s of max :%s\n [%s] \n...%s' % (count, total, bar, status))

main()
