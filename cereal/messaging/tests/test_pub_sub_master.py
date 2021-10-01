#!/usr/bin/env python3
import random
import time
import unittest

import cereal.messaging as messaging
from cereal.messaging.tests.test_messaging import events, random_sock, random_socks, \
                                                  random_bytes, random_carstate, assert_carstate, \
                                                  zmq_sleep


class TestSubMaster(unittest.TestCase):

  def setUp(self):
    # ZMQ pub socket takes too long to die
    # sleep to prevent multiple publishers error between tests
    zmq_sleep(3)

  def test_init(self):
    sm = messaging.SubMaster(events)
    for p in [sm.updated, sm.rcv_time, sm.rcv_frame, sm.alive,
              sm.sock, sm.freq, sm.data, sm.logMonoTime, sm.valid]:
      self.assertEqual(len(p), len(events))

  def test_init_state(self):
    socks = random_socks()
    sm = messaging.SubMaster(socks)
    self.assertEqual(sm.frame, -1)
    self.assertFalse(any(sm.updated.values()))
    self.assertFalse(any(sm.alive.values()))
    self.assertTrue(all(t == 0. for t in sm.rcv_time.values()))
    self.assertTrue(all(f == 0 for f in sm.rcv_frame.values()))
    self.assertTrue(all(t == 0 for t in sm.logMonoTime.values()))

    for p in [sm.updated, sm.rcv_time, sm.rcv_frame, sm.alive,
              sm.sock, sm.freq, sm.data, sm.logMonoTime, sm.valid]:
      self.assertEqual(len(p), len(socks))

  def test_getitem(self):
    sock = "carState"
    pub_sock = messaging.pub_sock(sock)
    sm = messaging.SubMaster([sock,])
    zmq_sleep()

    msg = random_carstate()
    pub_sock.send(msg.to_bytes())
    sm.update(1000)
    assert_carstate(msg.carState, sm[sock])

  # TODO: break this test up to individually test SubMaster.update and SubMaster.update_msgs
  def test_update(self):
    sock = "carState"
    pub_sock = messaging.pub_sock(sock)
    sm = messaging.SubMaster([sock,])
    zmq_sleep()

    for i in range(10):
      msg = messaging.new_message(sock)
      pub_sock.send(msg.to_bytes())
      sm.update(1000)
      self.assertEqual(sm.frame, i)
      self.assertTrue(all(sm.updated.values()))

  def test_update_timeout(self):
    sock = random_sock()
    sm = messaging.SubMaster([sock,])
    for _ in range(5):
      timeout = random.randrange(1000, 5000)
      start_time = time.monotonic()
      sm.update(timeout)
      t = time.monotonic() - start_time
      self.assertGreaterEqual(t, timeout/1000.)
      self.assertLess(t, 5)
      self.assertFalse(any(sm.updated.values()))

  def test_alive(self):
    pass

  def test_ignore_alive(self):
    pass

  def test_valid(self):
    pass

  # SubMaster should always conflate
  def test_conflate(self):
    sock = "carState"
    pub_sock = messaging.pub_sock(sock)
    sm = messaging.SubMaster([sock,])

    n = 10
    for i in range(n+1):
      msg = messaging.new_message(sock)
      msg.carState.vEgo = i
      pub_sock.send(msg.to_bytes())
      time.sleep(0.01)
    sm.update(1000)
    self.assertEqual(sm[sock].vEgo, n)


class TestPubMaster(unittest.TestCase):

  def setUp(self):
    # ZMQ pub socket takes too long to die
    # sleep to prevent multiple publishers error between tests
    zmq_sleep(3)

  def test_init(self):
    messaging.PubMaster(events)

  def test_send(self):
    socks = random_socks()
    pm = messaging.PubMaster(socks)
    sub_socks = {s: messaging.sub_sock(s, conflate=True, timeout=1000) for s in socks}
    zmq_sleep()

    # PubMaster accepts either a capnp msg builder or bytes
    for capnp in [True, False]:
      for i in range(100):
        sock = socks[i % len(socks)]

        if capnp:
          try:
            msg = messaging.new_message(sock)
          except Exception:
            msg = messaging.new_message(sock, random.randrange(50))
        else:
          msg = random_bytes()

        pm.send(sock, msg)
        recvd = sub_socks[sock].receive()

        if capnp:
          msg.clear_write_flag()
          msg = msg.to_bytes()
        self.assertEqual(msg, recvd, i)


if __name__ == "__main__":
  unittest.main()
