#!/opt/bin/python
#
# vim: fileencoding=utf-8
#
 
#
""" mpl2 subtitles -> microdvd subtitles
#
 
#
 #    author: i0cus@jabster.pl
#
  #   license: http://creativecommons.org/licenses/by-nc-sa/3.0/deed.pl
#
"""
#
 
#
import shutil
#
import sys
#
import re
#
 
#
MPL2LINE = re.compile("\[(?P<start>\d+)\]\[(?P<stop>\d+)\](?P<line>.*)", re.S)
#
 
#
if not len(sys.argv) in (3, 4) or '-h' in sys.argv or '--help' in sys.argv:
#
    print "%s [FROMFILE] TARGETFILE FRAMERATE" % sys.argv[0]
#
    sys.exit(1)
#
else:
#
    if len(sys.argv) == 3:
#
        sys.argv.insert(1, sys.argv[1])
#
    try:
#
        FRAMERATE = float(sys.argv[3])
#
    except TypeError:
#
        print "%s [FROMFILE] TARGETFILE FRAMERATE" % sys.argv[0]
#
        sys.exit(1)
#
    reader, writer = open(sys.argv[1]), open('/tmp/t', 'w')
#
    for line in reader:
#
        try:
#
            group = MPL2LINE.match(line).groupdict()
#
            start = int(float(group["start"])*0.1*FRAMERATE) or 1
#
            stop = int(float(group["stop"])*0.1*FRAMERATE)
#
            rest = group["line"]
#
            writer.write("{%d}{%d}%s" % (start, stop, rest))
#
        except:
#
            writer.write(line)
#
    [fileobj.close() for fileobj in (reader, writer)]
#
    if sys.argv[1] == sys.argv[2]:
#
        shutil.copy(sys.argv[1], sys.argv[1]+".bak")
#
    shutil.copy('/tmp/t', sys.argv[2])
    