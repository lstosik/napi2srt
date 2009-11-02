#!/usr/bin/env python
#
# subconv v0.2.2 -- divx subtitles converter
# (w)by Pawel Stolowski
#       Julien Lerouge
#
# Released under terms of GNU GPL
#

import re, sys, getopt, string

def usage():
	sys.stderr.write("""
 subconv v0.2.2 -- DivX subtitles converter
 (w)by Pawel Stolowski <yogin@linux.bydg.org>
       Julien Lerouge  <julien.lerouge@free.fr>

 Usage: subconv [-i fmt|-o fmt|-a sec|-s sec|-S h:m:s[,h:m:s,...]] input [output1, output2, ...]
	
     -i fmt        input format (one of: srt, tmp, mdvd, sub2, auto; auto by default)
     -o fmt        output format (one of: tmp, srt; srt by default)
     -f fps        adjust fps rate for microdvd input subtitles (auto by default)
     -a sec        adjust subtitle delay in seconds (add)
     -s sec        adjust subtitle delay in seconds (sub)
     -S h:m:s,...  split subtitles in selected position(s); additional output file names must be specified
     -h            this help

""")



def detect_fps(list):
	"""
	Detect the FPS for a given input file
	input: contents of a file as list
	returns: FPS
	"""
	sys.stderr.write("FPS guessing, here are approximate length of file for several FPS :\n")
	most_current=[23.976,25.0,29.0]
	
	re_mdvd = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
	count = len(list) - 1
	m = re_mdvd.match(list[count])
	while not m:
		count = count - 1
		m = re_mdvd.match(list[count])
	last = int(m.group(2))
		
	for i in range(0,len(most_current)):
		sys.stderr.write(str(i)+" "+str(most_current[i])+" Fps -> ")
		tot_sec = int(last / most_current[i])
		min = tot_sec / 60
		sec = tot_sec % 60
		sys.stderr.write(str(min)+" min "+str(sec)+"sec\n")
	sys.stderr.write("Choice : ")
	choice=int(sys.stdin.readline().strip())
	if choice>=0 and choice<len(most_current):
		return most_current[choice]
	else:
		sys.stderr.write("Bad choice\n")
		sys.exit(1)


def detect_format(list):
	"""
	Detect the format of input subtitles file.
	input: contents of a file as list
	returns: format (srt, tmp, mdvd) or "" if unknown
	"""
	sys.stderr.write("Guessing subs format .")
	re_mdvd = re.compile("^\{(\d+)\}\{(\d*)\}\s*(.*)")
	re_srt = re.compile("^(\d+):(\d+):(\d+),\d+\s*-->.*")
	re_tmp = re.compile("^(\d+):(\d+):(\d+):(.*)")
	re_sub2 = re.compile("^(\d+):(\d+):(\d+)\.\d+\s*\,.*")
	while len(list) > 0 :
		sys.stderr.write(".")
		line = list.pop(0)
		if re_mdvd.match(line):
			sys.stderr.write(" mdvd\n")
			return "mdvd"
		elif re_srt.match(line):
			sys.stderr.write(" srt\n")
			return "srt"
		elif re_tmp.match(line):
			sys.stderr.write(" tmp\n")
			return "tmp"
		elif re_sub2.match(line):
			sys.stderr.write(" subviewer 2 format\n")
			return "sub2"
	return ""


def read_mdvd(list, fps):
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


def read_sub2(list):
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

def read_srt(list):
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
						#subt.append(string.replace(l[:-1], "\r", ""))
						subt.append(l.strip())
						l = list.pop(0)
					subtitles.append(subt)
	except IndexError:
		sys.stderr.write("Warning: it seems like input file is damaged or too short.\n")
	return subtitles

def read_tmp(list):
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

def to_tmp(list):
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


def to_srt(list):
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


def sub_add_offset(list, off):
	"""
	Adds an offset (in seconds, may be negative) to all subtitles in the list
	input: subtitles (internal format)
	returns: new subtitles (internal format)
	"""
	outl = []
	for l in list:
		l[0] += off
		l[1] += off
		if l[0] < 0:
			sys.stderr.write("Warning, negative offset too high, subs beginning at 00:00:00\n")
			l[0] = 0
		if l[1] < 0:
			sys.stderr.write("Warning, negative offset too high, subs beginning at 00:00:00\n")
			l[1] = 0
		outl.append(l)
	return outl

def sub_split(sub, times):
	"""
	Splits subtitles
	input: subtitles (internal format) and split positions (in seconds)
	returns: a list of lists with new subtitles
	"""
	pos = 0
	num = len(sub)
	
	while pos<num and sub[pos][0]<times[0]:
		pos += 1
	
	lists = [ sub[:pos] ]    # [subtitles1, subtitles2, ...]

	times.append(99999999)
	minussec = times.pop(0)
	
	for second in times:
		outl = []
		while pos<num and sub[pos][0]<second:
			subline = [sub[pos][0]-minussec] + [sub[pos][1]-minussec] + sub[pos][2:]
			if subline[0] < 0:
				subline[0] = 0
			if subline[1] < 0:
				subline[1] = 0
			outl.append(subline)
			pos += 1
		lists.append(outl)
		minussec = second
	return lists

def get_split_times(str):
	"""
	Converts comma-separated string of "xx:yy:zz,xx:yy:zz,..." times to list of times (in seconds)
	input: string of comma-separated xx:yy:zz time positions
	returns: list of times
	"""
	tlist = str.split(",")
	re1 = re.compile("^(\d+):(\d+):(\d+)")
	times = []
	for t in tlist:
		m = re1.match(t, 0)
		if not m:
			sys.stderr.write("Unknown time format\n")
			return []
		times.append(int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)))
	return times		


def read_subs(file,fmt,fps):
	"""
	Reads subtitles fomr file, using format fmt
	input : file name, format (srt,mdvd,tmp,auto)
	returns: list of subtitles in form: [[time in secs, line1, ...],[time in secs, line1, ...],....]
	"""
	src = open(file,'r')
	subs = src.readlines()
	src.close()
	if fmt == "tmp":
		return read_tmp(subs)
	elif fmt == "srt":
		return read_srt(subs)
	elif fmt == "mdvd":
		if fps == -1:
			fps = detect_fps(subs)
		return read_mdvd(subs, fps)
	elif fmt == "auto":
		return read_subs(file,detect_format(subs),fps)
	elif fmt == "sub2":
		return read_sub2(subs)
	else:
		sys.stderr.write("Input format not specified/recognized\n")
		sys.exit(1)


#
#-----------------------------------------------------------------------------------------


outfunc = {
  "srt":to_srt,
  "tmp":to_tmp}

infmt = "auto"
outfmt = "srt"
subdelay = 0
fps = -1
#out_to_file == 1 => output to a file, 0 => output stdout, -1 => Split, output to stdout not allowed
out_to_file = 0

try:
	opts, args = getopt.getopt(sys.argv[1:], 'i:o:a:s:S:f:h')
except getopt.GetoptError:
	usage()
	sys.exit(2)

splittimes = []

for opt, arg in opts:
	if opt == '-o':
		if outfunc.has_key(arg):
			outfmt = arg
		else:
			sys.stderr.write("Unknown output format.\n")
			sys.exit(1)
	elif opt == '-i':
		infmt = arg
	elif opt == '-a':
		subdelay = float(arg)
	elif opt == '-s':
		subdelay = -float(arg)
	elif opt == '-S':
		out_to_file = -1
		splittimes = get_split_times(arg)
	elif opt == '-f':
		fps = float(arg)
	elif opt == '-h':
		usage()
		sys.exit(1)
	  
#
# number of file names must be 2 + number of split-points
if len(args) == len(splittimes)+2:
	out_to_file = 1
elif len(args) == len(splittimes)+1 and out_to_file != -1:
	out_to_file = 0
else:
	sys.stderr.write("Too few file names given!\n")
	usage()
	sys.exit(1)

#
# read file
sub = read_subs(args.pop(0),infmt,fps)

#
# apply DELAY
if subdelay != 0:
	sub = sub_add_offset(sub, subdelay)

#
# apply SPLIT
if len(splittimes) == 0:
	sub_list = [sub]
else:
	sub_list = sub_split(sub, splittimes)

#
# save file(S)
for nsub in sub_list:
	s = outfunc[outfmt](nsub)
	if out_to_file == 1:
	   	dst = open(args.pop(0), 'w')
	 	dst.writelines(s)
   		dst.close()
	else:
		sys.stdout.writelines(s)

