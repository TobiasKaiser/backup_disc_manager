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

def create_index_recursive(subdir, root, json_dest, base_dict, counters, verbose):
	cur_dir=os.path.join(root, subdir)
	print "[D] Entering directory: %s"%cur_dir
	for filename in os.listdir(cur_dir):
		cur_file=os.path.join(cur_dir, filename)
		cur_s=os.lstat(cur_file)
		rel_filename=os.path.join(subdir, filename)

		if stat.S_ISDIR(cur_s.st_mode):
			create_index_recursive(rel_filename, root, json_dest, base_dict, counters, verbose)
			continue

		if (stat.S_ISCHR(cur_s.st_mode)
			or stat.S_ISBLK(cur_s.st_mode)
			or stat.S_ISFIFO(cur_s.st_mode)
			or stat.S_ISLNK(cur_s.st_mode)
			or stat.S_ISSOCK(cur_s.st_mode)):
			print "[E] Non-regular file encountered. Skipping"
			counters["errors"]+=1
			continue

		if verbose:
			print "[F] path=%s size=%s mtime=%s md5sum=%s "%\
				(rel_filename, cur_s.st_size, cur_s.st_mtime, md5sum)
		
		if rel_filename in json_dest:
			print "[E] Error: Trying to doulbe add path %s, skipping second occurence."%rel_filename
			counters["errors"]+=1
			continue

		md5sum=None
		if rel_filename in base_dict:
			previous=base_dict[rel_filename]
			if previous["size"]==cur_s.st_size and previous["mtime"]==cur_s.st_mtime:
				md5sum=previous["md5sum"]
				if verbose:
					print "[U] File %s from base dict unchanged."%rel_filename
			else:
				print "[M] File %s from base dict modified."%rel_filename
				counters["modified"]+=1
		else:
			if verbose:
				print "[U] New file %s found."%rel_filename
			counters["new"]+=1
		if not md5sum:
			md5sum=md5sum_of_file(cur_file)

		
		json_dest[rel_filename]={
			"size": cur_s.st_size,
			"mtime": cur_s.st_mtime,
			"md5sum": md5sum
		}
		counters["total"]+=1

def usage():
	print "Usage: backup_disc_indexer.py [-v] -o JSON_OUTFILE [-b JSON_BASEFILE | -B] FOLDER1 [ FOLDER2 [ FOLDER3 ] ]"

def main():
	optlist, folders_to_idx=getopt.getopt(sys.argv[1:], "o:b:vB")
	file_to_write=None
	Auto=1
	base_file=None
	verbose=False
	counters={"total":0, "modified":0, "new":0, "errors":0}
	for (opt, val) in optlist:
		if opt=="-o":
			file_to_write=val
		elif opt=="-b":
			if base_file:
				print "Error: -b and -B are mutually exclusive."
			base_file=val
		elif opt=="-B":
			if base_file:
				print "Error: -b and -B are mutually exclusive."
			base_file=Auto
		elif opt=="-v":
			verbose=True
		else:
			raise Exception("Weird arg found.")

	if not file_to_write:
		print "Error: Output file not specified."
		usage()
		sys.exit(1)

	if base_file:
		if base_file==Auto:
			base_file=file_to_write
		print "[L] loading base %s"%base_file
		with open(base_file) as f:
			base_dict=json.load(f)
	else:
		base_dict={}

	out_dict={}
	for folder in folders_to_idx:
		create_index_recursive("", folder, out_dict, base_dict, counters, verbose)
	json_out=json.dumps(out_dict, indent=4, sort_keys=True)
	f=open(file_to_write, "w")
	f.write(json_out)
	f.close() 

 	print counters

if __name__=="__main__":
	main()
