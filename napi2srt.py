#!/usr/bin/env python
"""
Pobieracz i konwerter napisow do SRT
by Sternik
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
    MPL2LINE = re.compile('\[(\d+)\]\[(\d+)\](.*)', re.S)
    FRAMERATE = float(fps)
    reader, writer = open(mpl2file), open('/tmp/t', 'w')

    for line in reader:
        print MPL2LINE.match(line).groupdict()
        try:
            group = MPL2LINE.match(line).groupdict()
            start = int(float(group["start"])*0.1*FRAMERATE) or 1
            stop = int(float(group["stop"])*0.1*FRAMERATE)
            rest = group["line"]
            writer.write("{%d}{%d}%s" % (start, stop, rest))
        except:
            writer.write(line)

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
    if not isMpl2(os.path.splitext(file)[0]+'.txt'):
        mpl2(os.path.splitext(file)[0]+'.txt', fps)

# Funkcja przetwarza pliki
def dosrt(files):
    sub = NapiProject()

    for file in files:
        print 'Processing %s...' % os.path.basename(file),
        # olewamy gdy napisy w formacie srt juz sa
        if os.path.isfile(os.path.splitext(file)[0]+'.srt'):
            print 'srt subtitles already exist'
            continue

        # jezeli sa napisy w txt to tylko konwerujemy
        elif os.path.isfile(os.path.splitext(file)[0]+'.txt'):
            print 'txt subtitle exist...'
            # TODO: konwersja
            txt2srt(file)
            continue

        # a tu gdy nie ma napisow sciagamy je i konwerujemy do formatu srt
        else:
            print 'Getting subtitle...',
            if (not sub.getnapi(file)):
                print 'DOWNLOADED...'
                # TODO: konwersja
                txt2srt(file)
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
