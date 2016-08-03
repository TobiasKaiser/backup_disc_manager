#!/usr/bin/python
import os
import os.path
import sys
import json
import getopt
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def ignore(path):
	path=os.path.split(path)
	filename=path[len(path)-1]
	if filename.lower() in (".ds_store", "thumbs.db"):
		return True
	return False

def md5_hash(path, json):
	return json['md5sum']

def name_size_time_hash(path, json):
	path=os.path.split(path)
	filename=path[len(path)-1]
	return "%s_%s_%s"%(filename,json["size"],int(json["mtime"]))

my_hash=None

def load_to_hash(filename, base_by_hash):
	print "loading downstream %s"%filename
	with open(filename) as f:
		by_path=json.load(f)

	for p, d in by_path.items():
		if ignore(p): continue
		if my_hash(p, d) in base_by_hash:
			print "Duplicate file: %s and %s"%(p, base_by_hash[my_hash(p, d)]['path'])

			continue
			
		base_by_hash[my_hash(p, d)]={
			'path':p,
			'mtime':d["mtime"],
			'size':d["size"],
			'source':filename
		}
	print "\tcompleted."

Missing, Partial, Full = 1,2,3

def hsize(size):
	B=float(size)
	KB=B/1024
	MB=KB/1024
	GB=MB/1024

	if GB>1:
		return "%.2f GB"%GB
	elif MB>1:
		return "%.2f MB"%MB
	elif KB>1:
		return "%.2f KB"%KB
	else:
		return "%i B"%size

class UFile:
	def __init__(self, parent, json_values):
		self.state=None
		self.parent=parent
		self.json_values=json_values
		self.isource=None
		self.source=None
		self.size=json_values['size']
	def short(self):
		return "[%s]"%{Missing:"M",Partial:"P",Full:"F"}[self.state]

	def long(self):
		if self.isource:
			return self.isource
		else:
			return "%s"%hsize(self.size)
	
	def show(self, indent=0, onlymissing=False):
		pass

	def makestate(self, dsbh, filename):
		mymd5=my_hash(filename, self.json_values)
		if mymd5 in dsbh:
			self.state=Full
			self.isource="%s:%s"%(dsbh[mymd5]["source"], dsbh[mymd5]["path"])
			self.source=dsbh[mymd5]["source"]
		else:
			self.state=Missing
		return self.state

class UDirectory:
	def __init__(self, parent):
		self.files={}
		self.state=None
		self.parent=parent
		self.message=None
		self.source=set()
		self.size=None
		self.collapsed=False


	def short(self):
		return "[%s]"%{Missing:"M",Partial:"P",Full:"F"}[self.state]

	def long(self):
		if self.message:
			return self.message+" "+hsize(self.size)
		else:
			return hsize(self.size)

	def show(self, indent=0, onlymissing=False):
		dtabs='|   '*(indent-1)+("+---"if indent>0 else "")
		ftabs='|   '*indent	
		for fn in sorted(self.files.keys()):
			node=self.files[fn]
			if (not node.short() in ("[M]", "[P]")) and onlymissing: continue
			tabs=dtabs if isinstance(node, UDirectory) else ftabs
			print "%s%s %s %s"%(tabs, node.short(), fn, node.long())
			node.show(indent+1, onlymissing)

	def purge(self, message):
		self.files={}
		self.message=message
		self.collapsed=True


	def makestate(self, dsbh, filename):
		if self.state:
			raise Exception("Attempt to run makestate twice")

		partials, missings, fulls=0,0,0
		self.size=0
		for fn, f in self.files.items():
			childstate=f.makestate(dsbh, fn)
			if childstate==Partial:
				partials+=1
			elif childstate==Missing:
				missings+=1
			elif childstate==Full:
				fulls+=1
				if isinstance(f.source, set):
					self.source.update(f.source)
				else:
					self.source.add(f.source)
			self.size+=f.size

		if partials>0:
			self.state=Partial
		elif missings>0 and fulls>0:
			self.state=Partial
		elif missings>0:
			self.state=Missing
			self.purge("%i missing files collapsed"%missings)
		elif fulls>0:
			self.state=Full
			self.purge("%i full files collapsed (backed by %s)"%(fulls, self.source))
		else:
			raise Exception("parent with no child")
		return self.state

def get_dir(d, rootdir):
	cur=rootdir
	for part in d:
		if not (part in cur.files):
			new=UDirectory(cur)
			cur.files[part]=new
		cur=cur.files[part]
	
	return cur

def usage():
	print "backup_disc_evaluator -u JSON_UPSTREAM [-s | -m] JSON_DOWNSTREAM1 [ JSON_DOWNSTREAM2 [ ... ] ]"


def main():
	if len(sys.argv)<=1:
		usage()
		sys.exit(1)

	optlist, json_downstream_files=getopt.getopt(sys.argv[1:], "smu:")

	hashing_method=None
	MetaDataBased,SumBased=1,2

	upstream_file=None
	for (opt, val) in optlist:
		if opt =="-u":
			if upstream_file:
				raise Exception("Too many -u")
			else:
				upstream_file=val
		elif opt=="-s":
			if hashing_method: raise Exception("Too many hashing methods")
			hashing_method=SumBased
		elif opt=="-m":
			if hashing_method: raise Exception("Too many hashing methods")
			hashing_method=MetaDataBased
		else:
			raise Exception("Unknown option")

	if not hashing_method:
		raise Exception("Please specify -s (sum hashing) or -m (meta data hashing)")

	global my_hash
	my_hash=md5_hash if hashing_method==SumBased else name_size_time_hash

	downstream_by_hash={}

	for filename in json_downstream_files:
		load_to_hash(filename, downstream_by_hash)

	if not upstream_file:
		raise Exception("No upstream specified.")
	print "loading upstream %s"%upstream_file
	with open(upstream_file) as f:
		upstream=json.load(f)
	print "\tcompleted."

	rootdir=UDirectory(None)
	for path in upstream.keys():
		if ignore(path): continue
		paths=path.split("/")
		dname, fname=paths[:-1], paths[-1]

		directory=get_dir(dname, rootdir)
		directory.files[fname]=UFile(directory, upstream[path])

	globalstate= rootdir.makestate(downstream_by_hash, "")

	print
	rootdir.show()
	print
	
	if globalstate==Full:
		print "Full backup found."
	elif globalstate==Partial:
		print "Partial backup found."
	elif globalstate==Missing:
		print "No backups found."
	print
	rootdir.show(onlymissing=True)

if __name__=="__main__":
	main()
