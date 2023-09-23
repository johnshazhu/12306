import urllib.parse
import sys
import html
import re

def escape(string):
    string = string.encode('unicode_escape').decode("utf-8")
    string = urllib.parse.quote(string, safe='\\')
    string = string.upper().replace('\\U', '%u')
    return string

def unescape(string):
    string = urllib.parse.unquote(string)
    quoted = html.unescape(string).encode(sys.getfilesystemencoding()).decode('utf-8')
    return re.sub(r'%u([a-fA-F0-9]{4}|[a-fA-F0-9]{2})', lambda m: chr(int(m.group(1), 16)), quoted)