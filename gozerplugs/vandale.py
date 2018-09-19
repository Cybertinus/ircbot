# plugins/vandale.py
# encoding: utf-8
#

__copyright__ = 'this file is in the public domain'

from gozerbot.commands import cmnds
from gozerbot.examples import examples
from gozerbot.generic import striphtml
from gozerbot.aliases import aliasset
import urllib, re

IsoHtmlDict = { "À":"&Agrave;","Á":"&Aacute;","Â":"&Acirc;",
	"Ã":"&Atilde;","Ä":"&Auml;","Å":"&Aring;",
	"Æ":"&AElig;","Ç":"&Ccedil;","È":"&Egrave;",
	"É":"&Eacute;","Ê":"&Ecirc;","Ë":"&Euml;",
	"Ì":"&Igrave;","Í":"&Iacute;","Î":"&Icirc;",
	"Ï":"&Iuml;","Ð":"&ETH;","Ñ":"&Ntilde;",
	"Ò":"&Ograve;","Ó":"&Oacute;","Ô":"&Ocirc;",
	"Õ":"&Otilde;","Ö":"&Ouml;","Ø":"&Oslash;",
	"Ù":"&Ugrave;","Ú":"&Uacute;","Û":"&Ucirc;",
	"Ü":"&Uuml;","Ý":"&Yacute;","Þ":"&THORN;",
	"ß":"&szlig;","à":"&agrave;","á":"&aacute;",
	"â":"&acirc;","ã":"&atilde;","ä":"&auml;",
	"å":"&aring;","æ":"&aelig;","ç":"&ccedil;",
	"è":"&egrave;","é":"&eacute;","ê":"&ecirc;",
	"ë":"&euml;","ì":"&igrave;","í":"&iacute;",
	"î":"&icirc;","ï":"&iuml;","ð":"&eth;",
	"ñ":"&ntilde;","ò":"&ograve;","ó":"&oacute;",
	"ô":"&ocirc;","õ":"&otilde;","ö":"&ouml;",
	"ø":"&oslash;","ù":"&ugrave;","ú":"&uacute;",
	"û":"&ucirc;","ü":"&uuml;","ý":"&yacute;",
	"þ":"&thorn;","ÿ":"&yuml;" }

SpecialCharsMap = {
		# special chars
		"&#36;":     '$',
		"&#37;":     '%',
		"&#38;":     '&',
		"&#39;":     '\'',
		"&#64;":     '@',
		"&#126;":    '~',
		"&#167;":    '�',
		"&#176;":    '�',
		"&#178;":    '�',
		"&#180;":    '0',
		"&#183;":    '|',
		"&#215;":    'x',
		"&#229;":    '�',
		"&#956;":    '�',
}

re_stress =  re.compile("<U>(.*)</U>")
url = "http://mobiel.vandale.nl/?zoekwoord=%s";

def handle_vandale(bot, ievent):
    try:
        woord = ievent.args[0]
	if "%" in woord:
	    woord = woord.replace("%", "%25")
    except IndexError:
        ievent.missing('<woord>')
        return

    try:
	f = urllib.urlopen(url % woord)
    except:
        ievent.reply('connection failed')
	return
	
    data = f.read()
    if "Geen resultaat." in data:
        ievent.reply('not found')
        return
    
    results = []
    pos = 0
    while (True):
#        spos = data[pos:].find("<BIG>")
#	spos = data[pos:].find("<table class=")
	spos = data[pos:].find("<span class=\"pnn4_k\">")
        if spos==-1:
	    break
#        epos = data[pos+spos:].find("</td></tr>")
#	epos = data[pos+spos:].find("</td></tr></table></div>")
	epos = data[pos+spos:].find("</div></div>")
	if epos==-1:
	    break
	rstr = data[pos+spos:pos+spos+epos]
	# convert special chars and isohtmlcodes
	for k, v in IsoHtmlDict.items():
	    if v in rstr:
	        rstr = rstr.replace(v, k)
	for k, v in SpecialCharsMap.items():
	    if k in rstr:
 	        rstr = rstr.replace(k, v)

        # stress
        if not bot.jabber:
            stress = re_stress.split(rstr)
            if len(stress)==3:
                rstr = "%s\037%s\037%s" % (stress[0], stress[1], stress[2])
        # strip html chars
	rstr = striphtml(rstr)
	# count
	if rstr.split(" ", 1)[0][-1] in "0123456789":
	    w, r = rstr.split(" ", 1)
	    rstr = "%s (%s) %s" % (w[:-1], w[-1], r)
        # bold
	brac = rstr.find(")1")
	if brac!=-1:
	    rstr = "%s .. %s" % (rstr[:brac+1], rstr[brac+1:])
	else:
	    rstr = "%s" % (rstr)
	results.append(rstr)
        pos = pos+spos+epos
    if results:
	ievent.reply(url % woord + ' ==>' + ' | '.join(results))
	return
    else:
        ievent.reply('not found')
        return

cmnds.add('vandale', handle_vandale, 'USER')
examples.add('vandale','Lookup <woord> in vandale .. use % for wildcards', 'vandale test%n')
aliasset('vd', 'vandale')
aliasset('woord', 'vandale')

