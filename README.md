# seqbox
local sequence management lightweight tools

## Database notes

* sample_source_identifier needs to be unique within a group
    * confirm this with the PI, Brigitte says that many of the older TB studies 
    and some of the COM studies don't go through PreLink.
* if you add an existing sample_source_identifier associated with a different 
project then that sample_source_identifier will be associated
with that project.
* projects (and hence samples, sample sources, etc) can't be 
shared between groups
* projects is an attribute of sample_source because it's the 
sample source which is the primary thing enrolled in the project,
not the sample itself
* we have raw sequencing class because what if we want to re-basecall the
same sequencing run?
* raw_sequencing_batch name has to be unique across all projects/groups
* How to handle multiple picks from same sample?
    * Multiple picks should be added as new samples, related to the same
    sample source of course. Ideally, the sample identifier will make it
    easy to see that they're multiple picks. E.g. BMD671-1, BMD671-2.
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
* if you're adding a covid readset, need to include the `-s` flag
(stands for SARS-CoV-2, `-c` already taken)
* add readsets expects to find a single fastq in the barcode
directory. need to combine the fastqs if the basecaller makes 
multiple.
* all the input fastqs for both nanopore and illumina need to 
be gzipped.


## tests

1. Test 1 tests multiple things i) that the todo list query is working ok 
ii) end to end testing for covid workflow

    a. `run_test_01.sh`

    b. uploads everything in `01.test_todo_list_query` dir
    
    c. run the query in `get_covid_todo_list.sql` and check 
    that it returns properly ordered todo list.
   
2. Test that not adding in duplicates of anything.

    a. `run_test_02.sh`