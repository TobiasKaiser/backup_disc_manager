# Backup Disc Indexer

The purpose of the two scripts in this package are to manage a growing collection of offline optical discs that mirrors a growing collection of data (like pictures and videos) stored on hard disk.

Index files of both the hard disk and the offline media should be kept in an index directory.

The Evaluator script allows you to see which parts of your data collection is already saved and which needs to be backed up, so that you can make the decision which data to burn to disc next. After burning a disc, you create a new index file of it. For burning discs, no specialized software is needed.

Advantages of this backup scheme are:
* Optical discs are cheap and some of them promise a long lifetime.
* While the Backup Disc Indexer helps you making your backups, you do not depend on it and switch back to creating backups without help
*
* The Backup Disc Manager can deal with it if the folder structure on the optical discs differs from the folder structure on hard disk. Files are only identified by either **checksum** or **filename, size and last modification time**

Empty files, empty folders, and very small folders, which are not typically found in photo and video collections, are not captured by the Backup Disc Manager. When archiving source code, system file or similar structures, it is recommended that you create a ZIP or TAR archive file first.

## Creating the index files

Run **backup_disc_indexer.py** to create an index of the directory /media/hdd/, and each time you add files or make changes on your hard disk:

```
./backup_disc_indexer.py -B -o /home/user/backup_disc_index/hdd.idx /media/hdd/
```

Create a backup of optical disc #123: 
```
./backup_disc_indexer.py -o /home/user/backup_disc_index/disc_123_`date +%Y%m%d`.idx /media/cdrom0/
```

## Finding what to backup next

Run **backup_disc_evaluator.py** to find out what you should back up next. [M] stands for missing, [P] stands for partial backup found, [F] stands for full backup found. 

```
./backup_disc_evaluator.py -m -u /home/user/backup_disc_index/hdd.idx /home/user/backup_disc_index/disc_*.idx
```

You might want to experiment with using -s instead of -m for checksum based file identification instead of metadata based file identification.

## Feedback

Please feel free to send experiences or comments to Tobias Kaiser, mail@tb-kaiser.de.
