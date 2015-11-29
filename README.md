# oversized_syringe
Modding tool for the Hyperdimension Neptunia series games; enable packing/unpacking of resources from the games' custom archive format

**under active developement and still experimental**

# Abstract

The games themselves run pretty well under wine, the existing modding tools, however, do not (neither kitserver nor the packer created by anon).

Since I wanted to try the new translation for ReBirth;2, I had to borrow a friend's PC in order to statically patch my game files.

However, since being dependant on that kind of sucks, I decided to make my own packing/unpacking tool, by reverse-engineering the game's archive format.

I was able to un-compress the files by using QuickBMS (which you should also check out), then it was just a matter of discovering the compression algorithm, comparing "before" and "after".

The file's directory and compression formats are pretty much understood now (I'd say 99.9%); the developement is now aimed at creating a stable and usable tool

# Correctness

I tried unpacking and repacking some of the game's archives for testing purposes, here's the results:

("the game" being Re;Birth 1 and 2, steam version)
* The original game file and the rebuilt version have the same size in bytes, however, the internal
    structure is a tad bit different, and thus they have different checksums. I blame that on the different
    ordering of the nodes in the Huffman tree, but that's absolutely not a problem.
* Anyway, after unpacking, the recursive checksums of the extracted folders do match
* Tests against the actual game still are ongoing (I like to live dangerously);
* So far I've found out that the order in the file-directory IDs is very important, since the game
    uses that ID, rather than the internal name, to identify a packed file.

# Dependancies

    PyQt4
    bitarray

# Usage

## CLI version

    ./oversized_syringe.py -h
    
The command line tool has 2 general usages:
#### Non-staging mode

For read-only operation of the archive, like listing its content and extracting specific/all files
    
#### Staging mode

git-like interface for staging and applying modifications to an existing/new pac files. It must be
explicitly enabled for each step via the *-S* option

The usual workflow is something like this:

    oversized_syringe.py -S PACFILE.pac
        
Initialize the staging environment, the staged pac-object is a copy of PACFILE's content.
If you want to create a wholly new pacfile, run:
    oversized_syringe.py -S
        
        
    oversized_syringe.py -S -a file/name.xyz
    oversized_syringe.py -S -m directory/
    oversized_syringe.py -S -r file/name.xyz
    
Add a file (-a), merge a directory (-m), remove a file (-r)
        
When merging, the file with conflicting names will be staged for replacement
        
    oversized_syringe.py -S -u file/name.xyz
    
Undo (-u) the modifies (add/replace/delete) staged for file/name.xyz
        
The internal name (the name of the file inside the pac archive's directory) is translated directly from the filesystem path passed as an argument (with eventual conversion of slashes into backslashes). It is often useful to set a base-directory: basically, the path of the base-dir is subtrcted from the file's, and the result is used as the internal name:

    oversized_syringe.py -S -B extracted/ -a extracted/file/name.xyz
        
the file will be added as "file\name.xyz"
    
When you're done:
    
    oversized_syringe.py -S -c
    
Commit (-c) the modifies, meaning that the staged modifies will be applied to the staged pac-object
    
    oversized_syringe.py -S -w NEWFILE.pac
    
Finally, begin the compression of a new pacfile, using the previously build staged object as model.

If something went wrong during the process, you can reset the staging environment by deleting the .ovs_staging file.

The file will also be deleted once the write (-w) operation was completed with success.
    
    
## GUI version

Launch the script without arguments
The gui is composed of a package-view panel, a filesystem-view panel, and a staging-view panel.

![GUI preview](https://github.com/agentOfChaos/oversized_syringe/blob/master/readme.png)

The useges for the gui and the cli are pretty similar:
#### Extraction

After selecting a destination directory in the filesystem panel, you can either run "extract all" from the menu-bar, or cherry pick desired files (right click on the file > "Extract file/s")

#### Edit / create

From the menubar, you can either load an existing .pac file, or create a new one.
To add files to the package, right click on them from the filesystem-view, and choose "Import file/s".
Directories can also be "merged", meaning that their content will be added to the archive.
To remove files from the package, right click on them from the package-view, and choose "Stage file/s for deletion".

All those modifies are simply put into the temporary (staging) area, which shows which files will be added, replaced or deleted. If you wish to undo a staged modify, select it in the staging area, and right click > "Undo".

To actually apply those changes to the package, hit "commit" in the menu bar.

Finally, to create the actual .pac file, hit "write" in the menu bar.

**warning: in case you are editing an existing .pacfile, do not overwrite it**

# Roadmap

1. Extensive testing
2. Test support for other OSes
3. .cpk file support

# Thanks to

[Luigi Auriemma](aluigi.altervista.org)

[Idea Factory International](http://www.ideafintl.com/)