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

def usage():
	print "backup_disc_evaluator (-m JSON_DEST | -a JSON_DEST) JSON_BASE1 [ JSON_BASE2 [ ... ] ]"

def load_to_hash(filename, base_by_hash):
	print "loading downstream %s"%filename
	with open(filename) as f:
		by_path=json.load(f)

	for p, d in by_path.items():
		if ignore(p): continue
		if d['md5sum'] in base_by_hash:

			print "Duplicate file: %s and %s"%(p, base_by_hash[d['md5sum']]['path'])

			continue
			
		base_by_hash[d['md5sum']]={
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
	
	def show(self, indent=0):
		pass

	def makestate(self, dsbh):
		mymd5=self.json_values['md5sum']
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

	def short(self):
		return "[%s]"%{Missing:"M",Partial:"P",Full:"F"}[self.state]

	def long(self):
		if self.message:
			return self.message+" "+hsize(self.size)
		else:
			return hsize(self.size)

	def show(self, indent=0):
		dtabs='|   '*(indent-1)+("+---"if indent>0 else "")
		ftabs='|   '*indent	
		for fn in self.files.keys():
			node=self.files[fn]
			tabs=dtabs if isinstance(node, UDirectory) else ftabs
			print "%s%s %s %s"%(tabs, node.short(), fn, node.long())
			node.show(indent+1)

	def purge(self, message):
		self.files={}
		self.message=message


	def makestate(self, dsbh):
		if self.state:
			raise Exception("Attempt to run makestate twice")

		partials, missings, fulls=0,0,0
		self.size=0
		for f in self.files.values():
			childstate=f.makestate(dsbh)
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

def main():
	if len(sys.argv)<=1:
		usage()
		sys.exit(1)

	optlist, json_downstream_files=getopt.getopt(sys.argv[1:], "u:")

	upstream_file=None
	for (opt, val) in optlist:
		if opt in "-upstream":
			if upstream_file:
				raise Exception("Too many -l")
			else:
				upstream_file=val
		else:
			raise Exception("Unknown option")

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

	globalstate= rootdir.makestate(downstream_by_hash)

	rootdir.show()

	if globalstate==Full:
		print "Full backup found."
	elif globalstate==Partial:
		print "Partial backup found."
	elif globalstate==Missing:
		print "No backups found."

if __name__=="__main__":
	main()