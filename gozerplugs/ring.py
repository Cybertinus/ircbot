# myplugs/asno.py
#

from gozerbot.commands import cmnds
from gozerbot.examples import examples

from twisted.conch.ssh import transport, userauth, connection, common, keys, channel
from twisted.internet import defer, protocol, reactor

name = 'ring'
__revision__ = '$Id: asno.py 261 2010-12-01 12:22:37Z sten $'
__copyright__ = """
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <sten@blinkenlights.nl> wrote this module. As long as you retain this notice
 * you can do whatever you want with this stuff. If we meet some day, and you
 * think this stuff is worth it, you can buy me a beer in return.
 * Sten Spans
"""

class RingTransport(transport.SSHClientTransport):
    def verifyHostKey(self, hostKey, fingerprint):
        # MITM ftw!
	return defer.succeed(True)

    def connectionSecure(self):
        self.requestService(
            RingUserAuth(USER, RingConnection()))

class RingUserAuth(userauth.SSHUserAuthClient):
    def getPublicKey(self):
	path = os.path.expanduser('~/.ssh/id_rsa') 
	# this works with dsa too
	# just change the name here and in getPrivateKey
	if not os.path.exists(path) or self.lastPublicKey:
	    # the file doesn't exist, or we've tried a public key
	    return
	return keys.Key.fromFile(filename=path+'.pub').blob()

    def getPrivateKey(self):
	path = os.path.expanduser('~/.ssh/id_rsa')
	return defer.succeed(keys.Key.fromFile(path).keyObject)

class RingConnection(connection.SSHConnection):
    def serviceStarted(self):
        self.openChannel(PingChannel(conn = self))

class PingChannel(channel.SSHChannel, args):
    name = 'session'

    def openFailed(self, reason):
        print 'echo failed', reason

    def channelOpen(self, ignoredData):
        self.data = ''
        d = self.conn.sendRequest(self, 'exec', 
	    common.NS('bot-ping'), wantReply = 1)
        d.addCallback(self._cbRequest)

    def _cbRequest(self, ignored):
        self.write(args)
        self.conn.sendEOF(self)

    def dataReceived(self, data):
        self.data += data

    def closed(self):
        print 'got data from cat: %s' % repr(self.data)
        self.loseConnection()
        reactor.stop()

class Results():
    def __init__(self, results):
	self.results = results
	self.lock = threading.Lock()
    def __setitem__(self, key, value):
	with self.lock:
	    self.results{key} = value
    def __len__(self):
	return len(self.results)


class Ping(threading.Thread):
    def __init__ (self, counter, server, args):
	threading.Thread.__init__(self)
	self.counter = counter
	self.server = server
	self.args = args

    def run(self):
	protocol.ClientCreator(reactor, RingTransport).connectTCP(self.server, 22)
	reactor.run()

	except socket.error, (value,message):
	    pass

	self.results{server} = result


def handle_ping(bot,ievent):
    """ ring-ping a host """
    try:
	arg = ievent.args[0]
    except IndexError:
	ievent.missing('<host>')
	return

    results = Results(servers)
    # start the servers
    for server in servers:
	Ping(results).start()

    while len(results) > len(servers):
	sleep 0.1

    for result in results:
	if result == None:
	    ievent.reply("%s not found" % arg)
	    return

    ievent.reply(prepare_string(result))

cmnds.add(name + "-ping", handle_ping, 'USER')
examples.add(name, 'ping a host', name + '-ping kame.org')

