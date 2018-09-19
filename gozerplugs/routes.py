# myplugs/routes.py
#

from gozerbot.config import config
from gozerbot.generic import rlog
from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.datadir import datadir
from gozerbot.periodical import periodical

import os, re, time, string, sqlite3, urllib2
from stat import *

name = 'routes'
__revision__ = '$Id: routes.py 204 2009-04-14 20:10:38Z sten $'
__copyright__ = """
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <sten@blinkenlights.nl> wrote this module. As long as you retain this notice
 * you can do whatever you want with this stuff. If we meet some day, and you
 * think this stuff is worth it, you can buy me a beer in return.
 * Sten Spans
"""

def init():
    global perm, db

    perm = 'USER'

    db = {}
    db['file'] = datadir + os.sep + name + '.sqlite'
    db['url']  = "http://ams-9.net/data/" + name + '.sqlite'
    db['refresh'] = 86400

    # read config
    if config[name + '_perm']:
	perm = config[name + '_perm']

    rlog(10, name, 'perm set to: %s' % perm)

    if config[name + '_database']:
	db['file'] = config[name + '_database']

    rlog(10, name, 'database set to: %s' % db['file'])

    # update the database
    if not os.path.exists(db['file']):
	db['age'] = ''
    else:
	age = os.stat(db['file'])[ST_MTIME]
	db['age'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(age))

    fetch_database()
    db['jid'] = periodical.addjob(db['refresh'], 0, fetch_database, name)

    # register commands
    cmnds.add("route", handle_addr, perm)
    examples.add("route", 'lookup an IP', name + ' 66.66.66.66')


def shutdown():
    periodical.killjob(db['jid'])


def fetch_database():
    req = urllib2.Request(db['url'])
    req.add_header('If-Modified-Since', db['age'])

    try:
	response = urllib2.urlopen(req)
    except urllib2.URLError, e:
	if e.code == 304:
	    rlog(10, name, 'database is up to date')
	else:
	    rlog(10, name, 'error updating database (HTTP %s)' % e.code)
	return

    db['age'] = response.info()['Last-Modified']
    rlog(10, name, 'fetched new database (modified %s)' % db['age'])

    file = open(db['file'], 'w')
    file.write(response.read())
    file.close()


def lookup(addr):
    con = sqlite3.connect(db['file'])
    c = con.cursor()

    if addr.find(":") == -1:
	if not valid_v4(addr):
	    return

	long = 0
	for octet in addr.split('.'):
	    long <<= 8
	    long |= int(octet)

	    c.execute(""" SELECT r.net || '/' || r.mask, r.asno,
			     s.rir, s.date, s.policy
		      FROM routes AS r, rirs AS s 
		      WHERE r.type=? AND r.start <= ? AND r.end >= ?
		      AND s.start <= r.start AND s.end >= r.end
		      ORDER BY r.mask DESC LIMIT 1""", ("ipv4", long, long))

    result = c.fetchone()
    con.close()

    if result == None:
	return
    else:
	return result


def prepare_string(arr):
    result = ', '.join([str(x) for x in arr if x])
    return result


def handle_addr(bot,ievent):
    """ lookup an IP """
    try:
	addr = ievent.args[0]
    except IndexError:
	ievent.missing('<IP>')
	return

    result = lookup(addr)

    if result == None:
	ievent.reply("%s is unknown" % addr)
	return
    else:
	str = prepare_string(result)
	ievent.reply(addr + " = " + str)

def valid_v4(address):
    parts = address.split(".")
    if len(parts) != 4:
	return False
    try:
	for item in parts:
	    if not 0 <= int(item) <= 255:
		return False
	return True
    except:
	return False

