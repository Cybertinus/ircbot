# myplugs/oui.py
#

from gozerbot.config import config
from gozerbot.generic import rlog
from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.datadir import datadir
from gozerbot.periodical import periodical

import os, re, time, string, sqlite3, urllib2
from stat import *

name = 'oui'
__revision__ = '$Id: oui.py 241 2009-11-16 13:23:51Z sten $'
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
    cmnds.add('mac', handle_mac, perm)
    examples.add('mac', 'lookup an macaddr', 'mac ff:ff:ff')
    cmnds.add('wwn', handle_wwn, perm)
    examples.add('wwn', 'lookup an macaddr', 'wwn 21:00:00:e0:8b:05:05:04')


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


def macparse(macaddr):
    """ try parsing an oui from a macaddr """ 

    input = ''
    oui = ''
    meta = []
    multicast = 0
    admindefined = 0

    # sanitize
    macaddr.upper()
    macaddr = macaddr.replace('-', ':')
    macaddr = re.sub('[^A-F0-9\:]', '', macaddr)

    # evil hack to make single digit bytes work
    for octet in (macaddr.split(':')):
	if len(octet) == 1:
	    input += "0%s" % octet
	else:
	    input += octet

    # return if the input is too short
    if len(input) < 6:
	return (None, None)
    else:
	macaddr = input

    # IPv6 multicast [RFC2464]
    if macaddr[0:4] == '3333':
	oui = "%s-%s-%s" % (macaddr[0:2], macaddr[2:4], macaddr[4:6])
	meta.append('multicast')
	return (oui, meta)

    byte = int(macaddr[0:2],16)
    if byte % 2 != 0:
	meta.append('multicast')
	multicast = 1
	byte -= 1

    if byte & 2 != 0:
	meta.append('admindefined')
	admindefined = 1
	byte -= 2

    oui = "%02X-%s-%s" % (byte, macaddr[2:4], macaddr[4:6])

    # IANA oui - RFC 5342
    if oui == '00-00-5E' and len(macaddr) == 12:
	if multicast:
	    # IPv4 multicast [RFC1112]
	    if int(macaddr[6:8], 16) <= int("7F", 16):
		addr = '224.%d.%d.%d' % (int(macaddr[6:8], 16),
			    int(macaddr[8:10], 16), int(macaddr[10:12], 16))
		meta.append('IPv4 ' + addr)

	    # MPLS multicast [RFC5332]
	    elif int(macaddr[6:8], 16) <= int('8F', 16):
		meta.append('MPLS [RFC5332]')

	# VRRP is only reserved for the non-multicast range
	if not multicast:
	    if macaddr[6:10] == '0001':
		meta.append('VRRP id %d' % int(macaddr[10:12],16))

    return (oui, meta)


def wwnparse(wwn):
    """ try parsing an oui from a wwn """ 

    input = ''
    oui = ''
    meta = []

    # sanitize
    wwn.upper()
    wwn = re.sub('[^A-F0-9\:]', '', wwn)

    # evil hack to make single digit bytes work
    for octet in (wwn.split(':')):
	if len(octet) == 1:
	    input += "0%s" % octet
	else:
	    input += octet

    # return if the input is too short
    if len(input) < 10:
	return (None, None)
    else:
	wwn = input

    if wwn[0:4] == '1000':
	meta.append('IEEE 803.2 standard 48 bit')
	oui = "%s-%s-%s" % (wwn[4:6], wwn[6:8], wwn[8:10])

    elif wwn[0] == '2':
	meta.append('IEEE 803.2 extended 48-bit ID')
	oui = "%s-%s-%s" % (wwn[4:6], wwn[6:8], wwn[8:10])

    elif wwn[0] == '5':
	meta.append('IEEE Registered Name')
	oui = "%s-%s-%s" % (wwn[1:3], wwn[3:5], wwn[5:7])

    elif wwn[0] == '6':
	meta.append('IEEE Registered Extended')

    return (oui, meta)


def lookup(oui, meta):
    vendor = 0

    # rfc based assignments
    if oui == '00-00-5E':
	return 'IANA'
    if oui[0:5] == '33-33':
	return 'IPv6'

    con = sqlite3.connect(db['file'])
    c = con.cursor()
    c.execute(""" SELECT vendor FROM oui WHERE oui = ? """, (oui,))
    result = c.fetchone()
    con.close()

    if result == None:
	return
    else:
	return result[vendor]


def prepare_string(arr):
    result = ', '.join([str(x) for x in arr if x])
    return result



def handle_mac(bot,ievent):
    """ lookup an macaddr """
    try:
	macaddr = ievent.args[0]
    except IndexError:
	ievent.missing('<macaddr>')
	return

    (oui, meta) = macparse(macaddr.upper())
    if not oui:
	ievent.reply("can't parse %s" % macaddr)
	return

    if meta:
	meta_str = ' (%s)' % prepare_string(meta)
    else:
	meta_str = ''

    vendor = lookup(oui, meta) 
    if not vendor:
	ievent.reply("unknown vendor%s" % meta_str)
	return

    ievent.reply("%s = %s%s" % (macaddr, vendor, meta_str))


def handle_wwn(bot,ievent):
    """ lookup an wwn """
    try:
	wwn = ievent.args[0]
    except IndexError:
	ievent.missing('<wwn>')
	return

    (oui, meta) = wwnparse(wwn.upper())
    if not oui:
	ievent.reply("can't parse %s" % wwn)
	return

    if meta:
	meta_str = ' (%s)' % prepare_string(meta)
    else:
	meta_str = ''

    vendor = lookup(oui, meta) 
    if not vendor:
	ievent.reply("unknown vendor%s" % meta_str)
	return

    ievent.reply("%s = %s%s" % (wwn, vendor, meta_str))

