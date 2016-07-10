#!/usr/bin/python
import os
import os.path
import sys
import json
import getopt

def ignore(path):
	path=os.path.split(path)
	filename=path[len(path)-1]
	if filename.lower() in (".ds_store", "thumbs.db"):
		return True
	return False

def usage():
	print "backup_disc_evaluator (-m JSON_DEST | -a JSON_DEST) JSON_BASE1 [ JSON_BASE2 [ ... ] ]"

def load_to_hash(filename, base_by_hash):
	print "loading %s"%filename
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

def main():
	if len(sys.argv)<=1:
		usage()
		sys.exit(1)

	optlist, json_base_files=getopt.getopt(sys.argv[1:], "m:a:")

	base_by_hash={}

	for filename in json_base_files:
		load_to_hash(filename, base_by_hash)

	base_hashset=set(base_by_hash.keys())

	for (opt, val) in optlist:
		if opt in ("-m", "-a"):
			dest_by_hash={}
			load_to_hash(val, dest_by_hash)
			dest_hashset=set(dest_by_hash.keys())
			selected=dest_hashset-base_hashset if opt=="-m" else base_hashset-dest_hashset
			base_of_selected=dest_by_hash if opt=="-m" else base_by_hash
			sel_paths=[]
			for hashval in selected:
				d=base_of_selected[hashval]
				sel_paths.append(d['path'])

			sel_paths.sort()
			for p in sel_paths:
				print(p)
		else:
			print "???"


if __name__=="__main__":
	main()