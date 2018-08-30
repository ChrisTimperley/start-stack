#!/usr/bin/env python

# attack.py
#
# Kevin Angstadt
# angstadt @ umich.edu
# University of Michigan
#
# A script for "protecting" a sphere around a given GPS coordinate.
# When the MAV enters the protected zone, it is guided back out of
# the region while being instructed to continue to the next waypoint.
import logging
import argparse
import collections
import contextlib
from math import *
import pymavlink.mavextra
import pymavlink.mavutil
import select
import socket
import time
import struct
import sys

lgr = logging.getLogger("attacker")
lgr.setLevel(logging.DEBUG)  # type: logging.Logger

log_to_stdout = logging.FileHandler('attack.log', mode='w')
log_to_stdout.setLevel(logging.DEBUG)
lgr.addHandler(log_to_stdout)

closing = contextlib.closing
mavextra = pymavlink.mavextra
mavutil = pymavlink.mavutil
namedtuple = collections.namedtuple

FakeGPS = namedtuple('FakeGPS', ['lat', 'lon', 'cog', 'alt'])


# Helper function to determine the bearing between two GPS coordinates
def bearing(GPS_RAW1, GPS_RAW2):
    '''bearing of GPS_RAW2 relative to GPS_RAW1'''
    lat1 = radians(GPS_RAW1.lat) * 1.0e-7
    lat2 = radians(GPS_RAW2.lat) * 1.0e-7
    lon1 = radians(GPS_RAW1.lon) * 1.0e-7
    lon2 = radians(GPS_RAW2.lon) * 1.0e-7

    x = sin(lon2 - lon1) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(lon2 - lon1)

    return degrees(atan2(x, y))


def main():
    print sys.argv

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baudrate", type=int, help="master port baud rate", default=57600)

    parser.add_argument("--master", required=True, help="serial device")
    parser.add_argument(
        "--port", required=True, type=int, help="port for server")
    parser.add_argument("--logfile", help="location to log information")
    parser.add_argument("--mavlog", required=True, help="tlog dump location")

    parser.add_argument(
        "--report-timeout",
        type=int,
        default=-1,
        help=
        "seconds to wait before reporting attack back to system.  -1 means don't report"
    )

    parser.add_argument("lat", type=float, help="latitude of point to protect")
    parser.add_argument(
        "lon", type=float, help="longitude of point ot protect")
    parser.add_argument(
        "radius", type=float, help="radius around point to protect")

    args = parser.parse_args()
    lgr.info("parsed arguments")

    enabled = False
    attack_happened = False

    # connect to mav
    with closing( mavutil.mavlink_connection(args.master, baud=args.baudrate)) as master:
        lgr.info("connect to master")
        with open(args.mavlog, "w"):
            pass
        with closing(mavutil.mavlink_connection(args.mavlog, write=True, input=False)) as logger:
            lgr.info("connected to mav log file")
            # data variables here
            # make up a fake gps coordinate to calculations
            protect = FakeGPS(args.lat * 1.0e7, args.lon * 1.0e7, 0, 10)

            restore_mode = None
            triggered = False

            time_of_attack = None

            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    server.bind(("0.0.0.0", args.port))
                except IOError as e:
                    lgr.exception("failed to connect to socket")
                    raise

                lgr.info("connected to socket")
                server.listen(1)
                lgr.info("reply from socket")
                conn, addr = server.accept()
                lgr.info("established connection over socket")
                with closing(conn) as conn:
                    with closing(conn.makefile()) as rc:
                        lgr.info("full connection")
                        while True:
                            lgr.info("waiting to read")
                            to_read, _, _ = select.select([master.fd, rc], [], [], 1)
                            lgr.info("read to read")

                            for f in to_read:
                                # check to see if this is a mavlink packet or a message from the server
                                if f == master.fd:
                                    lgr.info("received MAVLink message")

                                    # we are the mav
                                    loc = master.recv_match(type='GPS_RAW_INT')

                                    if loc is None:
                                        continue

                                    if not enabled:
                                        continue

                                    # calculate distance and bearing from protected point
                                    dist = mavextra.distance_two(loc, protect)
                                    deg = mavextra.wrap_360(bearing(protect, loc))

                                    print dist

                                    # if we are in the 'cone of influence'
                                    if dist <= args.radius and master.motors_armed():
                                        print "Incoming target at %.2f degrees and %.2f meters away." % (
                                            deg, dist)
                                        # we need to protect the point!

                                        attack_happened = True

                                        if time_of_attack is None:
                                            time_of_attack = time.time()

                                        # but first back up current mode
                                        # if restore_mode is None:
                                        #     master.recv_match(type='SYS_STATUS')
                                        #     restore_mode = master.flightmode
                                        #     # set mode for brake
                                        #     master.set_mode(17)
                                        #     logger.set_mode(17)

                                        # if the attack hasn't occurred yet
                                        if not triggered:
                                            print "triggered\n"
                                            val = 0xFFFFFFFF
                                            master.param_set_send('j', 50)
                                            logger.param_set_send('j', 50)
                                            triggered = True
                                            triggered = True

                                        # # We sleep for a moment to help the MAV slow down
                                        # time.sleep(1)
                                        # print "go"


                                    # elif restore_mode is not None:
                                    #     # We are finished
                                    #     print 'Done protecting'
                                    #     master.set_mode(restore_mode)
                                    #     logger.set_mode(restore_mode)
                                    #     restore_mode = None

                                else:
                                    lgr.info("received message from test harness")
                                    # message from the server
                                    msg = f.readline().strip().upper()
                                    print msg
                                    lgr.info("TH message: %s", msg)
                                    if msg == "START":
                                        enabled = True
                                    
                                    elif msg == "EXIT":
                                        print "we are done"
                                        logger.close()
                                        break
                                        
                                    elif msg == "CHECK":
                                        if attack_happened:
                                            rc.write("YES\n")
                                            rc.flush()
                                        else:
                                            rc.write("NO\n")
                                            rc.flush()

                                    # print "waiting for heartbeat"
                                    # master.recv_match(type="HEARTBEAT", blocking=True)
                                    # print "got heartbeat"

                            # check to see if we should be reporting
                            if time_of_attack is not None:
                                if (args.report_timeout >= 0
                                        and time.time() - time_of_attack >
                                        args.report_timeout):
                                    rc.write("ATTACK\n")
                                    rc.flush()
                                    args.report_timeout = -1


if __name__ == '__main__':
    main()
