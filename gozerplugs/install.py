# plugs/install.py
#
#

""" signature of downloaded plugins is verified by signature files """

__copyright__ = 'this file is in the public domain'

# wrapper for the GNU Privacy Guard
# (c) Wijnand 'tehmaze' Modderman - http://tehmaze.com
# BSD License

from gozerbot.config import config
from gozerbot.datadir import datadir
from gozerbot.generic import gozerpopen, rlog
import os
import re
import tempfile

class PgpNoPubkeyException(Exception):
    pass

class PgpNoFingerprintException(Exception):
    pass

class NoGPGException(Exception):
    pass

class Pgp(object):
    ''' Wrapper for the GNU Privacy Guard. '''   
 
    re_verify = re.compile('^\[GNUPG:\] VALIDSIG ([0-9A-F]+)', re.I | re.M)
    re_import = re.compile('^\[GNUPG:\] IMPORT_OK \d ([0-9A-F]+)', re.I | re.M)
    re_pubkey = re.compile('^\[GNUPG:\] NO_PUBKEY ([0-9A-F]+)', re.I | re.M)

    def __init__(self):
        self.homedir = os.path.join(datadir, 'pgp')
        if not os.path.exists(self.homedir):
            rlog(5, 'pgp', 'creating directory %s' % self.homedir)
            os.mkdir(self.homedir)
        if hasattr(config, 'pgpkeyserver'):
            self.keyserver = config.pgpkeyserver
        else:
            self.keyserver = 'pgp.mit.edu'
        # make sure the pgp dir is safe
        os.chmod(self.homedir, 0700)
        rlog(5, 'pgp', 'will be using public key server %s' % self.keyserver)

    def exists(self, keyid):
        (data, returncode) = self._gpg('--fingerprint', keyid)
        return returncode == 0

    def imports(self, data):
        tmp = self._tmp(data)
        (data, returncode) = self._gpg('--import', tmp)
        os.unlink(tmp)
        test_import = self.re_import.search(data)
        if test_import:
            fingerprint = test_import.group(1)
            return fingerprint
        return None

    def imports_keyserver(self, fingerprint):
        (data, returncode) = self._gpg('--keyserver ', self.keyserver, \
'--recv-keys', fingerprint)
        if returncode == 256:
            raise NoGPGException()
        return returncode == 0

    def remove(self, data):
        if len(data) < 8:
            return False
        (_, returncode) = self._gpg('--yes', '--delete-keys',  data)
        if returncode == 256:
            raise NoGPGException()
        return returncode == 0

    def verify(self, data):
        tmp = self._tmp(data)
        (data, returncode) = self._gpg('--verify', tmp)
        os.unlink(tmp)
        if returncode == 256:
            raise NoGPGException()
        if returncode not in (None, 0, 512):
            return False
        test_pubkey = self.re_pubkey.search(data)
        if test_pubkey:
            raise PgpNoPubkeyException(test_pubkey.group(1))
        test_verify = self.re_verify.search(data)
        if test_verify:
            return test_verify.group(1)

    def verify_signature(self, data, signature):
        tmp1 = self._tmp(data)
        tmp2 = self._tmp(signature)
        (data, returncode) = self._gpg('--verify', tmp2, tmp1)
        os.unlink(tmp2)
        os.unlink(tmp1)
        if returncode == 256:
            raise NoGPGException()
        if returncode not in (None, 0, 512):
            return False
        test_pubkey = self.re_pubkey.search(data)
        if test_pubkey:
            raise PgpNoPubkeyException(test_pubkey.group(1))
        test_verify = self.re_verify.search(data)
        if test_verify:
            return test_verify.group(1)
        return None
        
    def _gpg(self, *extra):
        cmnd = ['gpg', '--homedir', self.homedir, '--batch', '--status-fd', '1']
        cmnd += list(extra)
        rlog(0, 'pgp', 'executing: %s' % ' '.join(cmnd))
        try:
            proces = gozerpopen(cmnd, [])
        except OSError, ex:
            raise NoGPGException
        except Exception, ex:
            rlog(0, 'pgp', 'error running "%s": %s' % (cmnd, str(ex)))
            raise
        data = proces.fromchild.read()
        returncode = proces.close()
        rlog(0, 'pgp', 'return code: %s, data: %s' % (returncode, data))
        return (data, returncode)

    def _tmp(self, data):
        fdid, tmp = tempfile.mkstemp()
        fd = os.fdopen(fdid, 'w')
        fd.write(data)
        fd.close()
        return tmp

# these are the gozerbot.org plugin repositories
gozerbot_pgp_keys = {
    # gozerbot.org/plugs install key
    '5290D844CF600B6CA6AFF8952D6D437CC5C9C2B2': '''
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQGiBEZM0ZURBADomT07whLs4n/ml84aIl8Ch6ShngfaaOS12ZrBQVQ/VSh7zPOx
IzfhSmwDJAWLZOnnM5zAqWPuNSJa3hQzY/M+X7vv3/p7kkB54/5U6LW+8ODENnMe
yPJhbI7phlfeE+STK9hytC3W5+OSrQknXkwYm1bGOur0iiU4Nr16ePE19wCg4KIc
ecqxm1U2CRtVC6G3qrZpscMD/0loPcv6Yw7Sx+3UwgAFaOJNE73P+h87wz29WkKs
h8Sx/l+Zf2NW/cMUwR0OOQQpzXKtZ8mF/CuPY4YITThKEGh680dUecuGBk5k3LeE
ZuLCFagEwZDWqXq/rR7+v8KCaxHpsaoU9P9p3Z7mruvaTYFp+yNfIYAklYoVI2iO
pB9PA/94xF3Vsdm3rqT6MUCVbBLKRRNHh7RDiFhQb0GfoWQiae0ZdJO2zWKCprKc
cboswKVs0SEUAD30izAaMlfR/p/LrFDHYwr5bBm38xhRMgFxrqdV+5o1+bdYNGA6
dJc6XgDWhDHpErCDibGAugNfVCDPhTE1eKbQQXST1KHnhyOcWbQeQmFydCBUaGF0
ZSA8YmFydEBnb3plcmJvdC5vcmc+iGAEExECACAFAkZM0ZUCGwMGCwkIBwMCBBUC
CAMEFgIDAQIeAQIXgAAKCRAtbUN8xcnCslzoAKCq7QqTlT10I6WcDZddY9GqcKxp
VQCaAgX1r9e39X79HR3NxTU6EHgm1hm5Ag0ERkzRnxAIALEuEASs9rpQNcpn6+UJ
M43J6vu9qYPl6T4ljsTdsi11Lr7r2ltFmvu/RqA9R4M4QwS/JZjm71R3Ci0eJSnR
AlkhejYHn5TKJ5rzRO6EUL0Jd/Rwgk/9qivIyfKAW3A1To2JgRUP9WI19MKYu6e9
K5h3KNi/1FfpeOFptB9mHyXBO2rHR9gaN6Wu9uz+eOGlZCyhNRx1jlmVcKAudT2g
qg/8NsuiEmv9Wf/CMgYawyenqx8S7cYC5EvHEscIOI/8zma0/1JqD8vllbSh64Ih
fsaW3twx/2gAIgtxRSIW7RQuYhs+zBT2C+Sg91rEgGcXjaw+OW2OZJ4kq1Qba82V
UOcAAwUH/21DRtgKgAX6xk97l+6ItP19HrcmydxNh299BboSKJDh5RcO1H4xOYyx
8NCDLhluGNzqeKPbBeW60F3qpkoQMGD7XsVpfKFu4Umn2qtrZAlg6qucgF0476IO
rhvKskAbNMBlocKzxiT+Ruomkt0Bwa3S1owXlMFwImA8coiWCQ8QnbpvjsYW9OH4
AgznK5uXKWgMxlZ9SffU0IHXipl3TENXiIdSwUUc2gV5emV/ROFhASNl7YYxZhY6
ng8YRku3MXM2jN1S/gNX1hvcq20oFjucKx7YkkV1k23FKF6XK776bmD0hYiSH1e0
uSAlBPAgC5HPqMpFhfyeFnDW0N90DR6ISQQYEQIACQUCRkzRnwIbDAAKCRAtbUN8
xcnCsoVMAJ472BdMgh+eUJp0+rGCeQhLELJVlQCcCV1zrNw9yoxIGJYnMZZSn4V5
Yf8=
=UxRq
-----END PGP PUBLIC KEY BLOCK-----
''',
    # tehmaze.com/plugs install key
    'D561C5D7CD86CB3CCA1AB5512A22EC17F9EBC3D8': '''
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQGiBEZMjOARBACYqwLsv7AMOEHL4wspu0DVXwzVm3U3AU2LivHaJjj66zTd16K4
1QQ8CjdWVjMLOSH9tvj0Z7wbdyeQEjAxykgIgIUvQ0zuHgzqVsbpW//W/Noc1Z3K
MIEPBQIDdWM7Ln9+1jZAWIKU6oPU6F9Qt2/8o2NDc0w8O73NKgn/NGWtqwCglitS
SvUvpP3HZZ8aYwqjk51j0V8D/ilgVNkb/7FumD2yF1R48bJmbRaFu58Hu2IplRr0
cGHZ1ijCR8fWeMPGY3CakEOjxQa9IkNtoce/PGTgbIl+TLwXSdiiyu5xkEIt2HHm
F3lzLw2o6T59g2w22KpLeXMO02+LcNdsV/BOrhLiO7E/cDB7wBfd/BG3zNC9C2ln
cmL4BACL5SEaOE4BCRrOfWdDDUF9iiXGxpCErdxlwId9eFM5OMe48ZmB7oGY52dY
rzGK54bqkVxRf5MOcUy3IjulZcy/LcOmm+agNnbQPVTuWNfty8+pSs6cPnF2bBUN
xf+UEZnQRlUHokHBy20DMjV3v8jXMBtZxlB24EmMDE21nAofZrQxdGVobWF6ZS5j
b20gKGdvemVycGx1Z3MpIDxnb3plcnBsdWdzQHRlaG1hemUuY29tPohgBBMRAgAg
BQJGTIzgAhsDBgsJCAcDAgQVAggDBBYCAwECHgECF4AACgkQKiLsF/nrw9gngQCf
esACa4M8ZjvMul8xad4oIUHkMTYAn0+bZBN8ip10/5qIR/CdDvwSL56b
=RTHp
-----END PGP PUBLIC KEY BLOCK-----
''',
    # trbs his key
    'B2FF7E64254524AC21EF9B76FF52B757C5181C13': '''
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v1.4.6 (GNU/Linux)

mQGiBEjE3rURBACHzP3dPU2E8t62zZ+nzksHsmaV4ooJPoysEWWpG9SdC2MGuwQ7
cnhCWmhxee6VbZ+KbC+pIEpEXeFPK3yaOkO09A1/CKuFTwndDR6Xzy4c/7WauYxq
hmn5Q/eODoKYseRoGY65u/rpK1/8OlNxjQltr1Ysgw+GHfjkJK2pWNz3wwCgnVZK
p6TYgb9EHLSjqmXekaOMV5kD/iH10PJXj3V+ToZKrsumP3dxha2TICtWMAo6LHa0
Qwwkjag93Ji+5yyVM/9UrYzJlqLUapTDit4gmeRm+3Abz6zcOcemowIbNhl/AK8F
04JaLTr3uOkkBaVRaIYWWPU8pmq9qT2vcPXxYVE87IBURp9XyvEZrhI/DPCtvXsJ
ZB+3A/0UVOo5anIiejqxk99VB61wYD2jN5SUD/VctrhIJYs0PnNBbD3rKcFwURLy
WB2cBRXPHoFBOm8h1nWxG/vCMvJoLSI9oU7/AV7j0v6uLSrO0EP8AreQONJi0J29
mIjIvdCn/f7pmYXJIL+xo+B1H2yd8uCUT66R+byqTlaISOZGe7Q6QmFzIHZhbiBP
b3N0dmVlbiAoR296ZXJib3QgUGx1Z2lucykgPHYub29zdHZlZW5AZ21haWwuY29t
PohgBBMRAgAgBQJIxN61AhsjBgsJCAcDAgQVAggDBBYCAwECHgECF4AACgkQ/1K3
V8UYHBOjywCfUZUZL034A5FL5Dv6jW+ul5FVee8An29ig3yylumzZclKGqnnRn0S
eb72uQENBEjE3rcQBAC22r4DBZNX6F9LDwtEXLnRpDwP1lf9e5gvD9NMD++zvEfq
Ezu/1WCg2hgPSJEDlX0sCnCeqyIonl5/3UjPfug9ZtZDOPjZAl2BDIAptwhZoNSd
ypuC4xOyLog7CXpTO0xHQAG7RhBncU9ieenZQQzTV81nFuWe5Icy1espbAi8xwAD
BQP6AhoaTKoNv6/JbHrDAigC0mcS7KabeumkRnOCHcZVdPYumto3E63SHZtAXFxI
ldkoCOhYfuj/3nosydJcSX0EF2rZMr9p0Mc/N+I341DVagi2OlLRYsqqrBbPm37j
BQNEDl/OUHI17ckd45OqiZ2RYiZlbXBrInFyFNhxElTBeQeISQQYEQIACQUCSMTe
twIbDAAKCRD/UrdXxRgcE7s4AJ9UzkvCP/tiwzoqe5nQSBqMZAwfUACfS+KCdWq0
92kg/7BDhzoD5a25BkI=
=+OEG
-----END PGP PUBLIC KEY BLOCK-----
''',
    # snore his key
   '5121C252FF91E0BD':"""
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: SKS 1.0.10

mQGiBERp0bERBAD3MPp/WCvXGP2wMp3TvifsnuJi8gRm4XYodXTVCEViZ7nCHzrN7Szg6y8q
K1IWP5h6FUXZWV33irZ99FYObDYbRAfLc+MY521JN61tJvcwRP7MMu5N5WNBIwp4xW5qP+z4
vpO9PodoTBScw6QDBkYuE9j9USB2BMaudlfX1jAk2wCgnwH3Y8Kwe5MZZysoL3KU5/8NIisD
/1jgMlGefoCSfplc37tKMH0nVOo94HW4Y4XA0NXZZkCVuHZKIscrS0hwW/ss0WjMzGu7FtmU
X/F2tllKDgKcPEHFXsLhT6dgLxIuzuGYZgr9l42cCcfpgWQCAIcvGiuO7YmTt5cnaJLjQswM
BcuU78tTa61tWxaAdH+eNNHV/+qgA/0Yj6mOnwpi1Md22Q9L18lS+n6oSJTzv57VyJfjZPGV
dxGligaBL4uq6zdqb2X8x8tTSUHGCQ8Gl6v+FL1sWn+K3aoPtVcpxU1RYmJ7Zf83Sgdx8qaJ
kdcfMBosbgEll+znl+vTAswcMGoVr/CkGyfJAjtVplId648+hjtpdoqvK7QiU3RlbiBTcGFu
cyA8c3RlbkBibGlua2VubGlnaHRzLm5sPohGBBARAgAGBQJEadkEAAoJECbTIkEcy1BHmBwA
n0NERJ74tkxsP+TF1nZx8iZ+fQ/4AKCM2hHWi71sBC/eU4hezK0sErn6lYhGBBARAgAGBQJE
aj2gAAoJEJsNdpdhxXCtNSoAoIIljClzClz6pFK1GGpYIaJTbSnYAJ9Q1wbn+K6bYcULYpPp
okyqMom0OYhMBBMRAgAMBQJEa3OXBYMPB/oaAAoJEOyRFOLTMLr8JIoAnRF1ZsEzTROjG9FP
0kcnTYxRTp+rAJ9SIZTDED/C0JTX2FeVf/bK9cW7BYhmBBMRAgAmBQJEadGxAhsDBQkPCZwA
BgsJCAcDAgQVAggDBBYCAwECHgECF4AACgkQUSHCUv+R4L120ACeLhN7vpj4Tc0JoVhEhC2J
fXydwGUAni0P3WEcB2+I4XEAYvp7/RF6aJSTuQINBERp0vwQCADFtCUtwwwhCLvyp/4a/hGh
SOpnug41CdG6eULrCi/+mm88r1ANoz9MXRFu5wqxKSIAInsy+WmDc9b6+PBmAiiUsR8qCgot
AWkzWo8a2BAXFSH9QhZTlhdY6chVzUZ9v4r1tJ+aBcd6+baLefTUGqsqZYwnoEXPK+sGsJNP
m7dK2/9DmQrpE/+vzS4hhWLRfYBbYRyMpZrbksEQ32p4wH2Vv5aWYudPmXYSlH77wYl4++qg
LEXIs5NoMaKsQJG7rre7vjAtltfQIw9guRc8UgA3gfaoI4IAUTk6g6J6jKvgUFsGvVA2CC5q
IYkUZz/ffe12uExg7PxbKZ7GxtkjKInDAAMGCADBA1y1VUAw1wmcMFFRw/Tp5xAd1dy9oH3h
sdZHBOWH0OSTcRLe014h4pn82HPu4rJQKyvpP/0DjTs8QfmkPn8E5Pgr6MuvcyTvwaCXfwtU
gI5s95x4nMTtSgrOcOuDulyUuzSLjk+aDqkk78U/N1ck4ifr6PZhrB3CvOPt4YqAWVr+3Bcd
grNFNqH332fQlLoNNekva0W4ogTv2vYVUNa1LNlOjIldmwlITDPqdLJxQ3kRub/e3KJ1Li1g
hxYBTzLQYqoJ+WvF6J2IhmH5xo5lu/Gh7aIh50Keyt3ZjE7gK5oQUBozOprOIWx7whVjAu2/
ZKWRt0IWuWEOLrioyflKiE8EGBECAA8FAkRp0vwCGwwFCQ8JnAAACgkQUSHCUv+R4L2bYwCf
bqSE/brg8NBAjUB2Bly/GE15KOUAniH5CnF11sfqL3aUUVkW58X+OQLM
=A6aR
-----END PGP PUBLIC KEY BLOCK-----
"""
}

# initiate a Pgp instance and import the distkeys, if needed
pgp = Pgp()
for keyid, keydata in gozerbot_pgp_keys.iteritems():
    try:
        if not pgp.exists(keyid):
            pgp.imports(keydata)
    except NoGPGException:
        rlog(10, 'pgp', 'no pgp installed')
        break

from gozerbot.generic import geturl, geturl2, waitforuser, touch, lockdec, \
rlog, exceptionmsg, handle_exception, uniqlist
from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.plugins import plugins
from gozerbot.plughelp import plughelp
from gozerbot.aliases import aliasdel, aliasset
from gozerbot.utils.dol import Dol
from gozerbot.datadir import datadir
from gozerbot.utils.fileutils import tarextract
import re, urllib2, urlparse, os, thread, shutil

class Cfg(object):

    """ contains plugin version data """
    def __init__(self):
        self.data = {}

    def add(self, plugin, version):
        """ add plugin version """
        self.data[plugin] = version
        #self.save()

    def list(self):
        """ list plugin versions """
        return self.data

cfg = Cfg()
installlock = thread.allocate_lock()
locked = lockdec(installlock)

plughelp.add('install', 'install plugin from remote site')

installsites = ['http://gozerplugs.blinkenlights.nl']

class InstallerException(Exception):
    pass

class Installer(object):
    '''
    We're taking care of installing and verifying plugins.
    '''
    
    BACKUP_PATTERN = '%s~'
    SUPPORTED_EXT = ['tar', 'py'] # supported extensions, in this order

    def install(self, plugname, site=''):
        '''
        Install `plugname` from `site`. If no `site` is specified, we scan the list of
        pre-configured `installsites`.
        '''
        # check if logs dir exists if not create it
        if not os.path.isdir('myplugs'):
            os.mkdir('myplugs')
            touch('myplugs/__init__.py') 
        errors = [] 
        if plugname.endswith('.py'):
            plugname = plugname[:3]
        plugname = plugname.split(os.sep)[-1]
        plugdata = ""
        if not site:
            for site in installsites:
                try:
                    plugdata, plugsig, plugtype = self.fetchplug(site, plugname)
                    break # no exception? found it!
                except InstallerException, e:
                    errors.append(str(e))
        else:
                try:
                    plugdata, plugsig, plugtype = self.fetchplug(site, plugname)
                except InstallerException, e:
                    errors.append(str(e))
        if not plugdata:
            if errors:
                raise InstallerException(', '.join(str(e) for e in errors))
            else:
                raise InstallerException('nothing to do')
        # still there? good
        if self.validate(plugdata, plugsig):
            if plugtype == 'py':
                self.save_py(plugname, plugdata)
            elif plugtype == 'tar':
                self.save_tar(plugname, plugdata)
            if hasattr(plugdata, 'info') and plugdata.info.has_key('last-modified'):
                cfg.add(plugname, ['%s/%s.%s' % (site, plugname, plugtype), plugdata.info['last-modified']])
            return '%s/%s.%s' % (site, plugname, plugtype)
        else:
            raise InstallerException('%s.%s signature validation failed' % (plugname, plugtype))

    def fetchplug(self, site, plugname):
        '''
        Fetch the plugin with `plugname` from `site`, we try any extension available in
        `Installer.SUPPORTED_EXT`. We also fetch the signature file.
        '''
        errors = []
        if not site.startswith('http://'):
            site = 'http://%s' % site
        base = '%s/%s' % (site, plugname)
        for ext in self.SUPPORTED_EXT:
            try:
                plugdata, plugsig = self.fetchplugdata(base, ext)
                return plugdata, plugsig, ext
            except InstallerException, e:
                errors.append(str(e))
        raise InstallerException(errors)

    def fetchplugdata(self, base, ext='py'):
        '''
        Here the actual HTTP request is being made.
        '''
        url = '%s.%s' % (base, ext)
        plug = base.split('/')[-1]
        try:
            plugdata = geturl2(url)
        except urllib2.HTTPError:
            raise InstallerException("no %s" % os.path.basename(url))
        if plugdata:
            try:
                plugsig = geturl2('%s.asc' % url)
            except urllib2.HTTPError:
                raise InstallerException('%s plugin has no signature' % plug)
            else:
                return plugdata, plugsig

    def backup(self, plugname):
        '''
        Backup a plugin with name `plugname` and return if we backed up a file or
        directory, and what its original name was.
        '''
        oldtype = None
        oldname = os.path.join('myplugs', plugname)
        newname = self.BACKUP_PATTERN % oldname
        if os.path.isfile('%s.py' % oldname):
            newname = self.BACKUP_PATTERN % '%s.py' % oldname
            oldname = '%s.py' % oldname
            oldtype = 'file'
            if os.path.isfile(newname):
                os.unlink(newname)
            os.rename(oldname, newname)
        elif os.path.isdir(oldname):
            oldtype = 'dir'
            if os.path.isdir(newname):
                shutil.rmtree(newname)
            os.rename(oldname, newname)
        return oldtype, newname

    def restore(self, plugname, oldtype, oldname):
        '''
        Restore a plugin with `plugname` from `oldname` with type `oldtype`.
        '''
        newname = os.path.join('myplugs', plugname)
        if oldtype == 'dir':
            # remove partial 'new' data
            if os.path.isdir(newname):
                shutils.rmtree(newname)
            os.rename(oldname, newname)
        elif oldtype == 'file':
            newname = '%s.py' % newname
            if os.path.isfile(newname):
                os.unlink(newname)
            os.rename(oldname, newname)

    @locked
    def save_tar(self, plugname, plugdata):
        oldtype, oldname = self.backup(plugname)
        try:
            if not tarextract(plugname, str(plugdata), 'myplugs'): # because it is an istr
                raise InstallerException('%s.tar had no (valid) files to extract' % (plugname))
        except InstallerException:
            raise
        except Exception, e:
            self.restore(plugname, oldtype, oldname)
            raise InstallerException('restored backup, error while extracting %s: %s' % (plugname, str(e))) 

    def save_py(self, plugname, plugdata):
        oldtype, oldname = self.backup(plugname)
        try:
            plugfile = open(os.path.join('myplugs', '%s.py' % plugname), 'w')
            plugfile.write(plugdata)
            plugfile.close()
        except InstallerException:
            raise
        except Exception, e:
            self.restore(plugname, oldtype, oldname)
            raise InstallerException('restored backup, error while writing %s: %s' % (plugfile, str(e))) 

    def validate(self, plugdata, plugsig):
        fingerprint = pgp.verify_signature(plugdata, plugsig)
        if not fingerprint:
            return False
        return True
        
def update():
    """ update remote installed plugins """
    updated = []
    all = cfg.list()
    for plug in all.keys():
        try:
            if plug in plugins.plugdeny.data:
                continue
            data = geturl2(all[plug][0])
            if hasattr(data, 'info') and data.info.has_key('last-modified'):
                if data.info['last-modified'] > all[plug][1]:
                    updated.append(all[plug][0])
        except urllib2.HTTPError:
            pass
        except urllib2.URLError:
            pass
    return updated

def handle_install(bot, ievent):
    """ install <server> <dir> <plugin> .. install plugin from server """
    try:
        (server, dirr, plug) = ievent.args
    except ValueError:
        if 'install-plug' in ievent.origtxt:
            ievent.missing("<server> <dir> <plug>")
        else:
            ievent.missing("<server> <dir> <plug> (maybe try install-plug ?)")
        return
    if plug.endswith('.py'):
        plug = plug[:-3]
    plug = plug.split(os.sep)[-1]
    url = 'http://%s/%s/%s' % (server, dirr, plug)
    try:
        readme = geturl2(url + '.README')
        if readme:
            readme = readme.replace('\n', ' .. ')
            readme = re.sub('\s+', ' ', readme)
            readme += ' (yes/no)'
            ievent.reply(readme)
            response =  waitforuser(bot, ievent.userhost)
            if not response or response.txt != 'yes':
                ievent.reply('not installing %s' % plug)
                return
    except:
        pass
    installer = Installer()
    try:
        installer.install(plug, 'http://%s/%s' % (server, dirr))
    except InstallerException, e:
        ievent.reply('error installing %s: ' % plug, result=[str(x) for x \
in list(e)], dot=True)
        return
    except Exception, ex:
        ievent.reply(str(ex))
        return
    reloaded = plugins.reload('myplugs', plug)
    if reloaded:
        ievent.reply("%s reloaded" % ' .. '.join(reloaded))
    else:
        ievent.reply('reload of %s failed' % plug)

cmnds.add('install', handle_install, 'OPER')
examples.add('install', 'install <server> <dir> <plug>: install \
http://<plugserver>/<dir>/<plugin>.py from server (maybe try install-plug \
?)', 'install gozerbot.org plugs autovoice')


def handle_installplug(bot, ievent):
    """ remotely install a plugin """
    if not ievent.args:
        ievent.missing('<plugnames>')
        return
    notinstalled = []
    installed = []
    reloaded = []
    reloadfailed = []
    missing = []
    errors = {}
    reloaderrors = {}
    installer = Installer()
    for plug in ievent.args:
        ok = False
        url = ''
        plug = plug.split(os.sep)[-1]
        for site in installsites:
            try:
                readme = geturl2('%s/%s.README' % (site, plug))
                if readme:
                    readme = readme.replace('\n', ' .. ')
                    readme = re.sub('\s+', ' ', readme)
                    readme += ' (yes/no)'
                    ievent.reply(readme)
                    response =  waitforuser(bot, ievent.userhost)
                    if not response or response.txt != 'yes':
                        ievent.reply('not installing %s' % plug)
                        notinstalled.append(plug)
                        break
            except:
                pass
            try:
                url = installer.install(plug, site)
                if url:
                    rlog(10, 'install', 'installed %s' % url)
                    installed.append(plug)
                    break # stop iterating sites
            except NoGPGException, ex:
                ievent.reply("couldn't run gpg .. please install gnupg if you \
want to install remote plugins")
                return
            except Exception, ex:
                errors[site] = str(ex)
    for plug in installed:
        try:
            reloaded.extend(plugins.reload('myplugs', plug))
        except ImportError, ex:
            if 'No module named' in str(ex):
                mismod = str(ex).split()[3]
                rlog(10, 'plugins', 'missing %s for plugin %s' % (mismod, plug))
                missing.append(mismod)
        except Exception, ex:
            reloadfailed.append(plug)
            reloaderrors[plug] = exceptionmsg()
    if reloadfailed: 
        ievent.reply('failed to reload: ', reloadfailed, dot=True)
        ievent.reply('reload errors: ', reloaderrors)
        return
    if missing:
        ievent.reply('missing plugins: ', missing, dot=True)
        return
    if reloaded:
        ievent.reply('reloaded: ', reloaded, dot=True)
        return
    if errors:
        errordict = Dol()
        errorlist = []
        for i, j in errors.iteritems():
            errordict.add(j, i)
        for error, sites in errordict.iteritems():
            errorlist.append("%s => %s" % (' , '.join(sites), error)) 
        ievent.reply("errors: ", errors, dot=True)

cmnds.add('install-plug', handle_installplug, 'OPER', threaded=True)
examples.add('install-plug', 'install-plug <list of plugins> .. try to \
install plugins checking all known sites', '1) install-plug 8b 2) \
install-plug 8b koffie')
aliasdel('install-plug')
aliasset('install-defaultplugs', 'install-plug alarm idle remind quote karma infoitem log ops rss todo seen url snarf dns popcon udp')

def handle_installkey(bot, ievent):
    """ install a remote gpg key into the keyring """
    if not bot.ownercheck(ievent):
        return
    if len(ievent.args) != 1:
        return ievent.missing('<key id> or <key file url>')
    url = ievent.args[0]
    if url.startswith('http://'):
        try:
            pubkey = geturl2(url)
        except urllib2.HTTPError:
            return ievent.reply('failed to fetch key from %s' % ievent.args[0])
        except urllib2.URLError, ex:
            ievent.reply("there was a problem fetching %s .. %s" % (url, \
str(ex)))
            return
        fingerprint = pgp.imports(pubkey)
        if fingerprint:
            return ievent.reply('installed key with fingerprint %s' % \
fingerprint)
        else:
            return ievent.reply('no valid pgp public key found')
    if not re.compile('^[0-9a-f]*', re.I).search(ievent.args[0]):
        return ievent.reply('invalid key id') 
    if pgp.imports_keyserver(ievent.args[0]):
        return ievent.reply('imported key %s from %s' % \
(ievent.args[0].upper(), pgp.keyserver))
    ievent.reply('failed to import key %s from %s' % (ievent.args[0].upper(), \
pgp.keyserver))

cmnds.add('install-key', handle_installkey, 'OPER')
examples.add('install-key', 'install a pgp key', \
'1) install-key 2A22EC17F9EBC3D8 2) install-key \
http://pgp.mit.edu:11371/pks/lookup?op=get&search=0xF9EBC3D8')

def handle_installlist(bot, ievent):
    """ install-list .. list the available remote installable plugs """
    errors = []
    result = []
    if ievent.rest:
        sites = [ievent.rest, ]
    else:
        sites = installsites
    for i in sites:
        try:
            pluglist = geturl2(i)
        except Exception, ex:
            errors.append(i)
            continue
        result += re.findall('<a href="(.*?)\.py">', pluglist)
        try:
            result.remove('__init__')
        except ValueError:
            pass
    if result:
        result.sort()
        ievent.reply('available plugins: ', uniqlist(result), dot=True)
    if errors:
        ievent.reply("couldn't extract plugin list from: ", errors, dot=True)

cmnds.add('install-list', handle_installlist, 'OPER')
examples.add('install-list', 'list plugins that can be installed', \
'install-list')

def handle_installsites(bot, ievent):
    """ show from which sites one can install plugins """
    ievent.reply("install sites: ", installsites, dot=True)

cmnds.add('install-sites', handle_installsites, 'USER')
examples.add('install-sites', 'show verified sites', 'install-sites')

def handle_installclean(bot, ievent):
    import glob
    removed = []
    for item in glob.glob(Installer.BACKUP_PATTERN % os.path.join('myplugs', '*')):
        if os.path.isfile(item):
            os.unlink(item)
            removed.append(os.path.basename(item))
        elif os.path.isdir(item):
            shutil.rmtree(item)
            removed.append(os.path.basename(item))
    if removed:
        ievent.reply('removed: ', result=removed, dot=True)
    else:
        ievent.reply('nothing to do')

#cmnds.add('install-clean', handle_installclean, 'OPER')

def handle_installupdate(bot, ievent):
    """ update command for remote installed plugins """ 
    updating = update()
    update_pass = []
    update_fail = []
    plugs = []
    installer = Installer()
    if updating:
        updating.sort()
        ievent.reply('updating: %s' % ', '.join(updating))
        for release in updating:
            parts = urlparse.urlparse(release)
            what = parts[2].split('/')[-1].replace('.py', '')
            try:
                installer.install(what)
                update_pass.append(what)
            except Exception, ex:
                handle_exception()
                update_fail.append(release)
        update_pass.sort()
        update_fail.sort()
        if update_fail:
            ievent.reply("failed updating %s" % " .. ".join(update_fail))
        if update_pass:
            plugs = ['myplugs/%s.py' % plug for plug in update_pass]
            ievent.reply("reloading %s" %  " .. ".join(plugs))
            failed = plugins.listreload(plugs)
            if failed:
                ievent.reply("failed to reload %s" % ' .. '.join(failed))
                return
            else:
                ievent.reply('done')
    else:
        ievent.reply('no updates found') 

cmnds.add('install-update', handle_installupdate, 'OPER')
examples.add('install-update', 'update remote installed plugins', \
'install-update')

def handle_installversion(bot, ievent):
    """ show versions of installed plugins """
    all = cfg.list()
    plugs = all.keys()
    if plugs:
        plugs.sort()
        ievent.reply(', '.join(['%s: %s' % (all[plug][0], all[plug][1]) \
for plug in plugs]))
    else:
        ievent.reply('no versions tracked')

cmnds.add('install-version', handle_installversion, 'OPER')
examples.add('install-version', 'show version of remote installed plugins', \
'install-version')
