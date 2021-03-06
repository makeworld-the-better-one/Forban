# Forban - a simple link-local opportunistic p2p free software
#
# For more information : http://www.foo.be/forban/
#
# Copyright (C) 2009-2012 Alexandre Dulaunoy - http://www.foo.be/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import time
import os
import logging
import logging.handlers
import ConfigParser
import subprocess


def guesspath():
    global lpath
    pp = os.path.realpath(sys.argv[0])
    lpath = os.path.split(pp)
    bis = os.path.split(lpath[0])
    return bis[0]


def get_cjdns_peers():
    return subprocess.check_output(["/bin/bash", lpath[0] + "/cjdns_peers.sh"]).strip().split("\n")


config = ConfigParser.RawConfigParser()
config.read(os.path.join(guesspath(),"cfg","forban.cfg"))

try:
    forbanpath = config.get('global','path')
except ConfigParser.Error:
    forbanpath = os.path.join(guesspath())

try:
    announceinterval = config.getint('global','announceinterval')
except ConfigParser.Error:
    announceinterval = 10

try:
    indexrebuild = config.getint('global','indexrebuild')
except ConfigParser.Error:
    indexrebuild = 1

try:
    forbanshareroot = config.get('forban','share')
except ConfigParser.Error:
    forbanshareroot = os.path.join(forbanpath,"var","share/")

try:
    forbanlogginglevel = config.get('global','logging')
except ConfigParser.Error:
    forbanlogginglevel = "INFO"

try:
    forbanloggingsize = config.get('global','loggingmaxsize')
except ConfigParser.Error:
    forbanloggingsize = 100000


announceinterval = float(announceinterval)
forbanpathlib=os.path.join(forbanpath,"lib")
sys.path.append(forbanpathlib)

import announce
import index
import tools

forbanpathlog=os.path.join(forbanpath,"var","log")
if not os.path.exists(forbanpathlog):
    os.mkdir(forbanpathlog)

forbanpathlogfile=forbanpathlog+"/forban_announce.log"
flogger = logging.getLogger('forban_announce')

if forbanlogginglevel == "INFO":
    flogger.setLevel(logging.INFO)
else:
    flogger.setLevel(logging.DEBUG)

handler = logging.handlers.RotatingFileHandler(forbanpathlogfile, backupCount=5, maxBytes = forbanloggingsize)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
flogger.addHandler(handler)

if __name__ == "__main__":

    try:
        forbanname = config.get('global','name')
    except ConfigParser.Error:
        forbanname = tools.guesshostname()

    try:
        ipv6_disabled =  config.get('global' , 'disabled_ipv6')
        flogger.debug("Read ipv6_disabled")
    except ConfigParser.Error:
        ipv6_disabled = 0

    msg = announce.message(name=forbanname, dynpath=os.path.join(forbanpath,"var"))

    if ipv6_disabled == "1":
        flogger.info("forban_announce without ipv6")
        msg.disableIpv6()

    try:
        cjdns_peers = config.get('global', 'cjdns_peers')
        flogger.debug("cjdns_peers set to", cjdns_peers)
    except ConfigParser.Error:
        cjdns_peers = 1  # Announce to cjdns peers by default
        flogger.debug("cjdns_peers set to 1 by default")

    if cjdns_peers:  # Now confirm that the CJDNS peers script runs
        try:
            get_cjdns_peers()
        except subprocess.CalledProcessError:
            cjdns_peers = 0
            flogger.debug("get_cjdns_peers failed, resetting cjdns_peers to 0")

    try:
        destination = config.get('global', 'destination')
        flogger.debug("Read custom destinations: >" + destination + "<")
        destination = eval(destination)  # Make it a list instead of a string
        msg.setDestination(destination)
    except ConfigParser.Error:
        msg.setDestination()
        destination = ["255.255.255.255", "ff02::1"]

    forbanindex = index.manage(sharedir=forbanshareroot, forbanglobal=forbanpath)
    flogger.info("forban_announce starting...")

    announce.flogger = flogger

forbansharebundle = os.path.join(forbanshareroot, "forban")

# bundle directory includes static pages but also index from the
# Forban itself.

if not os.path.exists(forbansharebundle):
    os.mkdir(forbansharebundle)

intervalcounter = 1
while 1:
    # rebuild forban index (at startup always rebuild)
    if intervalcounter <= 1:
        forbanindex.build()
        intervalcounter = indexrebuild
        flogger.debug("Index rebuilt")
    if cjdns_peers:
    	# Recalculate CJDNS peers every time
        flogger.debug("CJDNS PEERS: " + str(get_cjdns_peers()))
	msg.setDestination(get_cjdns_peers() + destination)
    msg.gen()
    msg.auth(value=forbanindex.gethmac())
    flogger.debug(msg.get())
    msg.send()
    intervalcounter = intervalcounter - 1
    time.sleep(announceinterval)
