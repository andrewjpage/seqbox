# seqbox
local sequence management lightweight tools

## Database notes

### groups

* Group name should not have any spaces in because it's used for file path.

### sample_source
* sample_source_identifier needs to be unique within a group
    * confirm this with the PI, Brigitte says that many of the older TB studies 
    and some of the COM studies don't go through PreLink.
* if you add an existing sample_source_identifier associated with a different 
project then that sample_source_identifier will be associated
with that project.

### projects
* projects (and hence samples, sample sources, etc) can't be 
shared between groups
* projects is an attribute of sample_source because it's the 
sample source which is the primary thing enrolled in the project,
not the sample itself

###read set batch/raw sequencing batch
* raw_sequencing_batch name has to be unique across all projects/groups
* readset_batch_name and raw sequencing batch namespace is shared across all groups/institutions (i.e. has to be unique)

### readset/raw sequencing
* currently assuming that whenever you have new raw sequencing, 
you are also adding a new readset as well.
* if you add a new readset with the same raw sequencing 
(identified by the extraction information), then only the new readset
is added (and it is linked to the same raw_sequencing record)
* `add_readsets` is for when you want to specify the path to
the fastqs, `add_nanopore_default_readsets` is for when you 
want to pass the barcodes and the directory name. Seqbox will
assume that the data is organised in the default nanopore
output way.
* in the batch upload, if going to do the add_readsets then 
batch_directory is not used. It is there for if going to use
add_nanopore_default_readsets upload, which requires to 
know the batch_directory.
* the same sample should only be run once on each batch. i.e.
don't run the same sample on multiple barcodes on the same
batch.
* add readsets expects to find a single fastq in the barcode
directory. need to combine the fastqs if the basecaller makes 
multiple.
* all the input fastqs for both nanopore and illumina need to 
be gzipped.
* if the readset is not covid, it needs the date and 
extraction identifier of the corresponding extraction.

### adding to filestructure

* if you're adding nanopore default data, it doesn't matter whether or not you
include the covid flag.
* if you're not adding nanopore default data, you should only include the covid
flag if you're uploading covid data.

### COVID
* if you're adding a covid readset, need to include the `-s` flag
(stands for SARS-CoV-2, `-c` already taken)
* if the readset is COVID, it needs the date and pcr identifier of the 
corresponding tiling pcr. if the readset is not covid, it needs the date and 
extraction identifier of the corresponding extraction.

### multiple picks
* How to handle multiple picks from same sample?
    * Multiple picks should be added as new samples, related to the same
    sample source of course. Ideally, the sample identifier will make it
    easy to see that they're multiple picks. E.g. BMD671-1, BMD671-2.

### merging

* If want to merge a couple of readsets of teh same extract, then need to make a 
new readset batch, then a bunch of new readsets.

### adding artic nf results

* will only work if you added the nanopore data using "default" settings, as it 
needs the barcode.
* only works with nanopore
* sample name column has to have the barcode as the last element when split by 
underscores

## tests

1. Nanopore, default, covid. Test 1 tests multiple things i) that the todo list query is working ok 
ii) end to end testing for covid workflow, nanopore default.

    a. `run_test_01.sh`

    b. uploads everything in `01.test_todo_list_query` dir
    
    c. run the query in `get_covid_todo_list.sql` and check 
    that it returns properly ordered todo list.
   
2. Nanopore, default, covid. If we add the same records multiple times, what happens?

    a. `run_test_02.sh`
    
    b. uploads everything in `01.test_todo_list_query` dir **twice**
    should return successful uploads for everything once.
    and then failed uploads for everything the second time round.

3. Nanopore, default, not covid. Test adding in the multiples of things i.e. same sample source in multiple projects,
 multiple samples per sample source, multiple extracts per sample, etc.

    a. `run_test_03.sh`
    
    b. uploads everything in `03.test`
    
    c. run queries in `03.test/checking_outputs.sql`
       
4. Illumina, non-covid. Uses same samples/sample sources etc as test_03, but
with illumina data instead of nanopore.

    a. `run_test_04.sh`
    
    b. run queries in `04.test/checking_outputs.sql`

5. Nanopore, not default, non-covid. Same as test_03.

    a. `run_test_05.sh`
    
    b. run queries in `05.test/checking_outputs.sql`
    
6. nanopore, default, not covid. test for adding another readset to same raw sequencing.

7. nanopore, not default, not covid. test for adding another readset to same raw sequencing

## How to add a new table

1. Commit to the flask migrate repo?
2. In seqbox_cmd:
    a. add a new parser to main()
    b. add to run_command()
    c. add new function for processing the input file
3. In seqbox_utils:
    
    a. add a new get_* function
    
        i. this runs a check_* function
        
        ii. need to come back and check this function after we have added somethign
         to make sure it returns correctly when there is a match in the database
         
4. In models:
    a. add a new class to represent the table
    b. 
    
    
    