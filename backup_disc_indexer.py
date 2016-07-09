#!/usr/bin/python
import os
import os.path
import sys
import stat
import hashlib
import json
import getopt

chunk_size=1024*1024*4

def md5sum_of_file(cur_file):
	f=open(cur_file, "rb")
	hasher=hashlib.md5()
	while True:
		rchunk=f.read(chunk_size)
		if len(rchunk)==0:
			break
		else:
			hasher.update(rchunk)
	f.close()
	return hasher.hexdigest()

def create_index_recursive(subdir, root, json_dest):
	cur_dir=os.path.join(root, subdir)
	print "[D] Entering directory: %s"%cur_dir
	for filename in os.listdir(cur_dir):
		cur_file=os.path.join(cur_dir, filename)
		cur_s=os.lstat(cur_file)
		rel_filename=os.path.join(subdir, filename)

		if stat.S_ISDIR(cur_s.st_mode):
			create_index_recursive(rel_filename, root, json_dest)
			continue

		if (stat.S_ISCHR(cur_s.st_mode)
			or stat.S_ISBLK(cur_s.st_mode)
			or stat.S_ISFIFO(cur_s.st_mode)
			or stat.S_ISLNK(cur_s.st_mode)
			or stat.S_ISSOCK(cur_s.st_mode)):
			raise Exception("Non-regular file encountered. We have no way to handle this (yet).")

		md5sum=md5sum_of_file(cur_file)

		print "[F] path=%s size=%s mtime=%s md5sum=%s "%\
			(rel_filename, cur_s.st_size, cur_s.st_mtime, md5sum)
		
		if rel_filename in json_dest:
			print "ERROR: Trying to double add path"
			#raise Exception("Trying to double add path")

		json_dest[rel_filename]={
			"size": cur_s.st_size,
			"mtime": cur_s.st_mtime,
			"md5sum": md5sum
		}

def usage():
	print "Usage: backup_disc_indexer.py -o JSON_OUTFILE [-b JSON_BASEFILE] FOLDER1 [ FOLDER2 [ FOLDER3 ] ]"

def main():
	optlist, folders_to_idx=getopt.getopt(sys.argv[1:], "o:b:")
	file_to_write=None
	base_file=None
	for (opt, val) in optlist:
		if opt=="-o":
			file_to_write=val
		elif opt=="-b":
			base_file=val
		else:
			raise Exception("Weird arg found.")

	if base_file:
		raise NotImplementedError("Base file is not implemented yet.")

	if not file_to_write:
		print "Error: Output file not specified."
		usage()
		sys.exit(1)



	out_dict={}
	for folder in folders_to_idx:
		create_index_recursive("", folder, out_dict)
	json_out=json.dumps(out_dict, indent=4, sort_keys=True)
	f=open(file_to_write, "w")
	f.write(json_out)
	f.close()
 

if __name__=="__main__":
	main()
