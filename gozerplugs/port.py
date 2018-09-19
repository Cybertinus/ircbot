# myplugs/port.py
#

from gozerbot.config import config
from gozerbot.generic import rlog
from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.datadir import datadir
from gozerbot.periodical import periodical

import os, time, string, sqlite3, urllib2
from stat import *

name = 'port'
__revision__ = '$Id: port.py 190 2009-02-23 18:46:20Z sten $'
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
    cmnds.add('port',handle_port,'USER')
    examples.add('port','lookup iana ports by name or number','port 514')


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


def handle_port(bot,ievent):
    """ lookup an iana port  """
    if not ievent.rest:
        ievent.missing("<string>")
        return
    else:
        req = ievent.rest.strip()

    con = sqlite3.connect(db['file'])
    c = con.cursor()

    if req.isdigit():
	c.execute(""" SELECT port, proto, keyword, description FROM ports
		      WHERE port = ? ORDER BY port LIMIT 4 """, (req,))
	results = c.fetchall()
    else:
	lreq = '%%%s%%' % req
    	c.execute(""" SELECT port, proto, keyword, description FROM ports
		      WHERE keyword LIKE ? ORDER BY port LIMIT 4""", (lreq,))
	results = c.fetchall()

    if not results:
	ievent.reply('no port data available')
	return

    for (port, proto, keyword, descr) in results:
	reply = "%s/%s - %s" % (port, proto, keyword)
	if descr:
	    reply += " (%s)" % descr

	ievent.reply(reply)

    return

