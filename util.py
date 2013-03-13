import urllib2
import re
import htmlentitydefs


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text
    return re.sub("&#?\w+;", fixup, text)


# instead of presuming to predict what
# will be colored, make it easy to prep
# string elements
def colorize(text, color):
    colors = {
        "white": 0,
        "black": 1,
        "blue": 2,          # (navy)
        "green": 3,
        "red": 4,
        "brown": 5,         # (maroon)
        "purple": 6,
        "orange": 7,        # (olive)
        "yellow": 8,
        "lightgreen": 9,    # (lime)
        "teal": 10,         # (a green/blue cyan)
        "lightcyan": 11,    # (cyan) (aqua)
        "lightblue": 12,    # (royal)
        "pink": 13,         # (light purple) (fuchsia)
        "grey": 14,
        "lightgrey": 15,    # (silver)
    }
    if isinstance(color, str):
        color = colors[color]

    return "\x03" + str(color) + text + "\x03"


def pageopen(url):
    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urlbase = opener.open(url).read()
        urlbase = re.sub('\s+', ' ', urlbase).strip()
    except:
        return False

    return urlbase
