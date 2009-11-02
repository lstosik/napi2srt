#!/usr/bin/env python
"""
napi2srt

Downloader and converter to SRT subtitles from NapiProject.pl

2009-11-02 Pawel Sternal <sternik@gmail.com>
"""
import os
import re
import sys
import md5
import shutil
import urllib
import subprocess

### KONFIGURACJA ###
# Miejsce aplikacji p7zip (7z)
p7zip = "/opt/local/bin/7za"
# Rozszerzenia filmow
movie_ext = [".avi", ".mpg", ".mkv", ".mp4", ".rmvb", ".mov"]

# subconv v0.2.2 -- divx subtitles converter
# (w)by Pawel Stolowski
#       Julien Lerouge
class SubConv():
    def detect_format(self,list):
        """
        Detect the format of input subtitles file.
        input: contents of a file as list
        returns: format (srt, tmp, mdvd) or "" if unknown
        """
        re_mdvd = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
        re_srt = re.compile("^(\d+):(\d+):(\d+),\d+\s*-->.*")
        re_tmp = re.compile("^(\d+):(\d+):(\d+):(.*)")
        re_sub2 = re.compile("^(\d+):(\d+):(\d+)\.\d+\s*\,.*")
        while len(list) > 0 :
            line = list.pop(0)
            if re_mdvd.match(line):
                return "mdvd"
            elif re_srt.match(line):
                return "srt"
            elif re_tmp.match(line):
                return "tmp"
            elif re_sub2.match(line):
                return "sub2"
        return ""

    def read_mdvd(self,list,fps):
        """
        Read micro-dvd subtitles.
        input: contents of a file as list
        returns: list of subtitles in form: [[time_start in secs, time_end in secs, line1, ...],....]
        """
        re1 = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
        subtitles = []
        while len(list)>0:
            m = re1.match(list.pop(0), 0)
            if m:
                subt = [int(m.group(1)) / float(fps)]
                subt.append(int(m.group(2)) / float(fps))
                subt.extend(m.group(3).strip().split("|"))
                subtitles.append(subt)
        return subtitles

    def read_sub2(self,list):
        """
        Reads subviewer 2.0 format subtitles, e.g. :
            00:01:54.75,00:01:58.54
            You shall not pass!
        input: contents of a file as list
        returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
        """
        re1 = re.compile("^(\d+):(\d+):(\d+)\.(\d+)\s*\,\s*(\d+):(\d+):(\d+)\.(\d+).*$")
        subtitles = []
        try:
            while len(list)>0:
                m = re1.match(list.pop(0), 0)
                if m:
                    subt = [int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/100.0]
                    subt.append(int(m.group(5))*3600 + int(m.group(6))*60 + int(m.group(7)) + int(m.group(8))/100.0)
                    l = list.pop(0).strip()
                    lines = l.split("[br]")
                    for i in range(0,len(lines)):
                        subt.append(lines[i])
                    subtitles.append(subt)
        except IndexError:
            sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
        return subtitles

    def read_srt(self,list):
        """
        Reads srt subtitles.
        input: contents of a file as list
        returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
        """
        re1 = re.compile("^(\d+)\s*$")
        re2 = re.compile("^(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+).*$")
        re3 = re.compile("^\s*$")
        subtitles = []
        try:
            while len(list)>0:
                if re1.match(list.pop(0), 0):
                    m = re2.match(list.pop(0), 0)
                    if m:
                        subt = [int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/1000.0]
                        subt.append(int(m.group(5))*3600 + int(m.group(6))*60 + int(m.group(7)) + int(m.group(8))/1000.0)
                        l = list.pop(0)
                        while not re3.match(l, 0):
                            subt.append(l.strip())
                            l = list.pop(0)
                        subtitles.append(subt)
        except IndexError:
            sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
        return subtitles

    def read_tmp(self,list):
        """
        Reads tmplayer (tmp) subtitles.
        input: contents of a file as list
        returns: list of subtitles in form: [[time_dep, time_end, line1, ...],[time_dep, time_end, line1, ...],....]
        """
        re1 = re.compile("^(\d+):(\d+):(\d+):(.*)")
        subtitles = []
        subs={}
        while len(list)>0:
            m = re1.match(list.pop(0), 0)
            if m:
                time = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3))
                if subs.has_key(time) :
                    subs[time].extend(m.group(4).strip().split("|"))
                else:
                    subs[time] = m.group(4).strip().split("|")

        times = subs.keys()
        times.sort()
        for i in range(0,len(times)):
            next_time = 1;
            while not subs.has_key(times[i]+next_time) and next_time < 4 :
                next_time = next_time + 1
            subt = [ times[i] , times[i] + next_time]
            subt.extend(subs[times[i]])
            subtitles.append(subt)
        return subtitles

    def to_tmp(self,list):
        """
        Converts list of subtitles (internal format) to tmp format
        """
        outl = []
        for l in list:
            secs = l[0]
            h = int(secs/3600)
            m = int(int(secs%3600)/60)
            s = int(secs%60)
            outl.append("%.2d:%.2d:%.2d:%s\n" % (h,m,s,"|".join(l[2:])))
        return outl

    def to_srt(self,list):
        """
        Converts list of subtitles (internal format) to srt format
        """
        outl = []
        count = 1
        for l in list:
            secs1 = l[0]
            h1 = int(secs1/3600)
            m1 = int(int(secs1%3600)/60)
            s1 = int(secs1%60)
            f1 = (secs1 - int(secs1))*1000
            secs2 = l[1]
            h2 = int(secs2/3600)
            m2 = int(int(secs2%3600)/60)
            s2 = int(secs2%60)
            f2 = (secs2 - int(secs2))*1000
            outl.append("%d\n%.2d:%.2d:%.2d,%.3d --> %.2d:%.2d:%.2d,%.3d\n%s\n\n" % (count,h1,m1,s1,f1,h2,m2,s2,f2,"\n".join(l[2:])))
            count = count + 1
        return outl

    def read_subs(self,file,fmt,fps):
        """
        Reads subtitles fomr file, using format fmt
        input : file name, format (srt,mdvd,tmp,auto)
        returns: list of subtitles in form: [[time in secs, line1, ...],[time in secs, line1, ...],....]
        """
        src = open(file,'r')
        subs = src.readlines()
        src.close()
        if fmt == "tmp":
            return self.read_tmp(subs)
        elif fmt == "srt":
            return self.read_srt(subs)
        elif fmt == "mdvd":
            if fps == -1:
                fps = self.detect_fps(subs)
            return self.read_mdvd(subs, fps)
        elif fmt == "auto":
            return self.read_subs(file,self.detect_format(subs),fps)
        elif fmt == "sub2":
            return self.read_sub2(subs)

    def convert(self, file, fps):
        outfunc = {
          "srt":self.to_srt,
          "tmp":self.to_tmp}

        infmt = "auto"
        outfmt = "srt"
        out_to_file = 0
        fps = float(fps)

        # read file
        sub = self.read_subs(os.path.splitext(file)[0]+'.txt',infmt,fps)
        sub_list = [sub]

        # save file(S)
        for nsub in sub_list:
            s = outfunc[outfmt](nsub)

            dst = open(os.path.splitext(file)[0]+'.srt', 'w')
            dst.writelines(s)
            dst.close()

# reversed napi 0.16.3.1
# by gim,krzynio,dosiu,hash 2oo8
class NapiProject():
    def f(self, z):
        idx = [ 0xe, 0x3,  0x6, 0x8, 0x2 ]
        mul = [   2,   2,    5,   4,   3 ]
        add = [   0, 0xd, 0x10, 0xb, 0x5 ]

        b = []
        for i in xrange(len(idx)):
            a = add[i]
            m = mul[i]
            i = idx[i]

            t = a + int(z[i], 16)
            v = int(z[t:t+2], 16)
            b.append( ("%x" % (v*m))[-1] )

        return ''.join(b)

    def getnapi(self, file):
        d = md5.new();
        d.update(open(file).read(10485760))

        str = 'http://napiprojekt.pl/unit_napisy/dl.php?l=PL&f=%s&t=%s&v=other&kolejka=false&nick=&pass=&napios=%s' % (d.hexdigest(), self.f(d.hexdigest()), os.name)

        open('napisy.7z', 'w').write(urllib.urlopen(str).read())

        if os.path.splitext(file)[1] == '.rmvb':
            subtitle = file[:-4]+'txt'
        else:
            subtitle = file[:-3]+'txt'

        if (not os.system('%s x -y -so -piBlm8NTigvru0Jr0 napisy.7z 2>/dev/null > "%s"' % (p7zip, subtitle))):
            os.remove('napisy.7z')
            return 0
        else:
            os.remove(subtitle)
            os.remove('napisy.7z')
            return 1

# Funkcja sprawdza czy plik jest filmem, w zaleznosci jakie ma rozszerzenie
# Rozszerzenia ustala sie w movie_ext
def isMovie(file):
    if os.path.splitext(file)[1] in movie_ext: return file

# Funkcja konwertuje napisy z formatu MPL2 na MicroDVD
def mpl2(mpl2file, fps):
    """ mpl2 subtitles -> microdvd subtitles
        author: i0cus@jabster.pl
        license: http://creativecommons.org/licenses/by-nc-sa/3.0/deed.pl
    """
    MPL2LINE = re.compile("\[(?P<start>\d+)\]\[(?P<stop>\d+)\](?P<line>.*)", re.S)
    FRAMERATE = float(fps)
    reader, writer = open(mpl2file), open('/tmp/t', 'w')

    for line in reader:
        group = MPL2LINE.match(line).groupdict()
        start = int(float(group["start"])*0.1*FRAMERATE) or 1
        stop = int(float(group["stop"])*0.1*FRAMERATE)
        rest = group["line"]
        writer.write("{%d}{%d}%s" % (start, stop, rest))

    [fileobj.close() for fileobj in (reader, writer)]

    shutil.copy('/tmp/t', mpl2file)

# sprawdzamy czy napisy *.txt sa w formacie mpl2
def isMpl2(file):
    f = open(file, 'r')
    line = f.readline()
    f.close

    if re.match(r'\A\[', line):
        return True

# wyciagamy fps filmu
def getFps(file):
    fps = subprocess.Popen("file "+file, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE).stdout.read().split()[8]

    if fps == '23.98':
        fps = '23.976'

    return fps

# Funkcja konwertujaca *.txt do *.srt
def txt2srt(file):
    # sprawdzamy fps filmu
    if os.path.splitext(file)[1] == '.avi':
        fps = getFps(file)
    else:
        fps = '23.976'

    # jezeli napisy sa w formacie mpl2 - konwertujemy je do mdvd
    if isMpl2(os.path.splitext(file)[0]+'.txt'):
        mpl2(os.path.splitext(file)[0]+'.txt', fps)

    # Konwerujemy z txt -> srt
    sub = SubConv()
    sub.convert(file,fps)

# Funkcja przetwarza pliki
def dosrt(files):
    sub = NapiProject()

    for file in files:
        print 'Processing %s...' % os.path.basename(file),
        # olewamy gdy napisy w formacie srt juz sa
        if os.path.isfile(os.path.splitext(file)[0]+'.srt'):
            print 'SRT still exist'
            continue

        # jezeli sa napisy w txt to tylko konwerujemy
        elif os.path.isfile(os.path.splitext(file)[0]+'.txt'):
            print 'txt subtitle exist...',
            txt2srt(file)
            print 'CONVERT to SRT'
            continue

        # a tu gdy nie ma napisow sciagamy je i konwerujemy do formatu srt
        else:
            print 'Getting subtitle...',
            if (not sub.getnapi(file)):
                print 'DOWNLOADED...',
                txt2srt(file)
                print 'CONVERTED to SRT'
            else:
                print 'NO SUBTITLE'

    return 0

# Funkcja glowna
def main():
    # sprawdzamy czy poprawnie jest odpalany skrypt
    if len(sys.argv) == 2:
        fd = sys.argv[1]
    else:
        print 'usage: %s movie_file or path_with_movies' % os.path.basename(sys.argv[0])
        return 0

    # sprawdzamy, czy jest zainstalowany p7zip
    popen = subprocess.Popen(p7zip, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if (not popen.stdout.read()):
        print 'You must install p7zip to use this program.'
        return 0

    # sprawdzamy czy plik lub katalog istnieja
    if not os.path.isdir(fd) and not os.path.isfile(fd):
        print 'File or path doesn\'t exist'
        return 0

    # jezeli jest to plik, to dopasowujemy napisy
    elif not os.path.isdir(fd) and os.path.isfile(fd):
        filelist = [fd]
        dosrt(filelist)
        return 0

    # a tu lecimy rekursywnie po katalogach
    elif os.path.isdir(fd):
        filelist = []
        space = re.compile(r" ", re.I).search
        for root, subFolders, files in os.walk(fd):
            for file in files:
                # zamieniamy spacje na kropki
                if isMovie(file) and space(file):
                    newfile = file.replace(' ', '.')
                    os.rename(os.path.join(root,file), os.path.join(root,newfile))
                    filelist.append(os.path.join(root,newfile))
                # jezeli plik jest filmem, dodajemy go do listy
                elif isMovie(file): filelist.append(os.path.join(root,file))

        dosrt(filelist)
        return 0

# START:
if __name__ == '__main__':
    sys.exit(main())
