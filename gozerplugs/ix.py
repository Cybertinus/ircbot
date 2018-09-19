# myplugs/ix.py
#

from gozerbot.config import config
from gozerbot.generic import rlog
from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.datadir import datadir
from gozerbot.periodical import periodical

import os, re, time, string, sqlite3, urllib2
from stat import *

name = 'ix'
__revision__ = '$Id: ix.py 255 2010-08-05 21:52:48Z sten $'
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
    for iname in list(db['file']):
	cmnds.add(iname, handle_ix, perm)
	examples.add(iname, 'lookup an %s port' % iname, '%s foobar' % iname)


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


def lookup(ix, input):

    con = sqlite3.connect(db['file'])
    c = con.cursor()

    c.execute(""" SELECT * FROM ix WHERE name = ? AND 
	    (asno = ? OR ipv4 = ? OR ipv6 = ? OR org = ?) """, 
	    (ix, input, input, input, input))
    results = c.fetchall()

    if not results:
	linput = '%%%s%%' % input
	c.execute(""" SELECT * FROM ix WHERE name = ? AND org LIKE ? """, 
	    (ix, linput))
	results = c.fetchall()

    con.close()
    return results


def list(filename):
    con = sqlite3.connect(filename)
    c = con.cursor()
    c.execute(""" SELECT DISTINCT(name) FROM ix """)
    results = c.fetchall()
    con.close()

    if results == None:
	return
    else:
	names = []
	for row in results:
	    names.append(row[0])
	return names


def prepare_string(arr):
    result = ', '.join([str(x) for x in arr if x])
    return result


def handle_ix(self, ievent):
    """ lookup an exchange port """
    try:
	input = ievent.args[0]
    except IndexError:
	ievent.missing('<string>')
	return

    ports = lookup(ievent.command, input)

    if not ports:
	ievent.reply("%s not found" % input)
	return

    lines = 0

    for port in ports:
	lines += 1
	result = prepare_string(port[2:])
	if lines < 5:
	    ievent.reply(result)
	else:
	    break

    if len(ports) >= 5:
	ievent.reply("(%s ports matched)" % len(ports))

