# seqbox
local sequence management lightweight tools

**this codebase is still in active development, breaking changes will occur**

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
* if you delete a project, then it won't cascade through to delete the sample sources
in the project.

### projects
* projects (and hence samples, sample sources, etc) can't be 
shared between groups
* projects is an attribute of sample_source because it's the 
sample source which is the primary thing enrolled in the project,
not the sample itself
* if you delete a project, then it won't cascade through to delete the sample sources
in the project.

### read set batch/raw sequencing batch
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
extraction identifier of the corresponding extraction. if it is covid then
need the tiling pcr date.
* negative controls/negative extractions should be assigned to sample sources and 
samples wiht the identifier "Neg_ex" (the underscore is important as sample names become 
paths, so shouldn't have spaces etc. they will all be grouped togehter into
those samples/sample sources, but will of course have different extractions. 
they can be assigned to thge same project/group as the run (or arbitrary, doesnt matter). 
* need extraction_from in readsets so that the db knows whether the join the extraction to a sample directly or to a culture


### covid confirmatory pcrs & other PCRs

* for pcrs, negative results should have their Ct field left blank.

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

```
conda activate seqbox
export DATABASE_URL="postgresql:///test_seqbox?host=/var/run/postgresql/"
sudo service postgresql start
export PYTHONPATH=~/code/seqbox/src/:$PYTHONPATH

sudo -u postgres createuser username
sudo -u postgres createdb test_seqbox
sudo -u postgres psql -c "grant all privileges on database test_seqbox to username;"
```



Before running tests run `export DATABASE_URL="postgresql:///test_seqbox"`, and also run `conda activate seqbox`.

1. Nanopore, default, covid. Test 1 tests multiple things i) that the todo list query is working ok 
ii) end to end testing for covid workflow, nanopore default.

    a. run `./test/01.test/setup.sh` and `./test/01.test/upload_a.sh`
    
    b. then run this query
    ```
    select sample.sample_identifier, sample.day_received, sample.month_received, sample.year_received, pr.pcr_result as qech_pcr_result, pr.ct as original_ct, project_name, e.extraction_identifier, DATE(e.date_extracted) as date_extracted, ccp.pcr_identifier, DATE(ccp.date_pcred) as date_covid_confirmatory_pcred,
    ccp.ct as covid_confirmation_pcr_ct, tp.pcr_identifier as tiling_pcr_identifier, DATE(tp.date_pcred) as date_tiling_pcrer, rsb.name as read_set_batch_name, r.readset_identifier
    from sample
    left join sample_source ss on sample.sample_source_id = ss.id
    left join sample_source_project ssp on ss.id = ssp.sample_source_id
    left join project on ssp.project_id = project.id
    left join pcr_result pr on sample.id = pr.sample_id
    left join extraction e on sample.id = e.sample_id
    left join covid_confirmatory_pcr ccp on e.id = ccp.extraction_id
    left join raw_sequencing rs on e.id = rs.extraction_id
    left join tiling_pcr tp on rs.tiling_pcr_id = tp.id
    left join raw_sequencing_batch rsb on rs.raw_sequencing_batch_id = rsb.id
    left join read_set r on rs.id = r.raw_sequencing_id
    order by sample.year_received desc, sample.month_received desc, sample.day_received desc
   ```
    Check that it gives this output:
   
    CMT15I,,,,Positive,15.4,covid sequencing,1,2021-06-01,1,2021-06-01,15.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,1
    CMT1XD,,,,Positive,15.4,covid sequencing,1,2021-06-01,1,2021-06-01,15.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,2
    CMT15J,,,,Positive,33.4,covid sequencing,1,2021-06-01,1,2021-06-01,33.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,3
    CMT15V,,,,Positive,22.5,covid sequencing,1,2021-06-01,1,2021-06-01,22.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,4
    CMT1KL,,,,Positive,38.5,covid sequencing,1,2021-06-01,1,2021-06-01,38.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,5
    CMT1KQ,,,,Positive,12.5,covid sequencing,1,2021-06-01,1,2021-06-01,12.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,6
    CMT16X,,,,Positive,12.4,covid sequencing,1,2021-06-01,1,2021-06-01,12.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,7
    CMT16E,,,,Positive,19.6,covid sequencing,1,2021-06-01,1,2021-06-01,19.6,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,8
    CMT15Q,,,,Negative,,covid sequencing,1,2021-06-01,1,2021-06-01,,,,,
    CPH121,,,,Positive,23.4,covid sequencing,1,2021-06-01,1,2021-06-01,23.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,9
    CMT163,,,,Positive,23.4,covid sequencing,1,2021-06-01,1,2021-06-01,23.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,10
    CMT16W,,,,Positive,23.4,covid sequencing,1,2021-06-01,1,2021-06-01,23.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,11

2. Illumina, models the default sequencing service (samples submitted for extraction, added to db, extractions added later), also tests the whole sample to extract flow.

    a. run setup.sh - wipes/makes the db, adds the group and project.
 
    b. run upload_a.sh - adds sample sources, samples, and cultures.

    c. run upload_b.sh - adds extractions and elutions to the cultures from upload_a (models common lab flow)
    
    d. run upload_c.sh - adds sample sources, samples, extractions, and elutions from whole_sample
    
    e. run query_a.sh - gets the "to sequence" list

    f. run upload_d.sh - add sequencing information to the samples/extractions from upload_a/b
    
    g. run upload_e.sh - add sample sources, samples, cultures and extractions when the client submits extractions from culture (testing this logic, rather than submitting extractions from whole_sample or cultures)
 
3. submitting samples only to keep track of, running query (which should be blank as these samples are not available for the lab guys to sequence) and then adding sample information and re-running query to check that the sample is now available for sequencing.

    a. run setup.sh - wipes/makes the db, adds the group and project.
 
    b. run upload_a.sh - adds sample sources, samples, and cultures.

    c. run `python src/scripts/seqbox_cmd.py query_info_on_all_samples` - should return nothing

    d. run upload_b.sh - adds extractions and elutions to the cultures from upload_a (models common lab flow)
    
    e. run `python src/scripts/seqbox_cmd.py query_info_on_all_samples` - should return one sample.


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
    
## Dependencies
* sudo apt-get install libxslt-dev libxml2-dev libpam-dev libedit-dev postgresql
* pip install pyyaml - tested v5.4.1
* pip install Flask - tested Flask-2.0.1
* pip install SQLAlchemy - tested SQLAlchemy-1.4.21
* pip install Flask-SQLAlchemy - tested Flask-SQLAlchemy-2.5.1
* Flask-Login-0.5.0
* Flask-Bootstrap-3.3.7.1
* Flask-Migrate-3.0.1
* Flask-WTF-0.15.1
* email-validator-1.1.3
* psycopg2==2.9.1

conda env create --name seqbox --file seqbox_conda_env.yaml

## combined input sheet explainer

We need information on four “classes” of thing – sample source, sample, extraction and tiling PCR. I’ve colour coded the attached template by these four classes.
 
The rationale, starting from the end of the process and working backwards, is:
 
We sequence the product of a tiling PCR reaction(s)
We do tiling PCR on an RNA extract from a sample
A sample is derived from a sample source.
Sample sources belong to projects (and have other characteristics we might want to capture).
 
Essential columns are; sample_source_identifier; sample_source_type, projects, group_name, institution, sample_identifier, date_extracted, extraction_identifier, date_tiling_pcred, tiling_pcr_identifier, tiling_pcr_protocol.
 
I recognise that this is quite a lot of info, but it means it should be robust to all kinds of repeats (if you re-do tiling PCR on the same extract, if you re-extract the same sample, if you take multiple samples from the same sample_source, etc).
 
Then, once the sequencing is done, there will be another spreadsheet to fill in with the sequencing run information.
 
Few other bits of info:
If you sampled the same site twice, those two samples should have the same sample_source_identifier.
Each individual sample should have a unique sample_identifier.
The extraction identifier column is only for if you do multiple extractions from the same sample on the same day, if you only do one sample on each date then this should always be `1`. The tiling_pcr identifier works in the same way.
 

## single sheet rationale

Ok, the overall information I need is the group name and project name. Then there are four separate spreadsheets which you need to fill in. I know it’s a lot, but it was designed for the COVID sequencing service so it’s quite granular.

The rationale is:

1.	We sequence the product of a tiling PCR reaction(s)
2.	We do tiling PCR on an RNA extract from a sample
3.	A sample is derived from a sample source.
4.	Sample sources belong to projects (and have other characteristics we might want to capture).

Each step in the process for a particular sample source/sample/extract/tiling PCR links to the previous step in the chain for a particular “sample”. So, when you enter the information for a tiling PCR reaction, you also need to tell the database which extract you did this reaction on. When you enter the information for the extraction, you need to tell it which sample you extracted from, and so on.

Then “sample source” information. This is for e.g. sites you’ve sampled. If you sample the same site twice it should have the same sample_source_identifier. Essential columns here are; sample_source_identifier; sample_source_type, projects, group_name, institution.

Then “sample” information. This is for each sample you’ve taken. Each individual sample should have a unique sample_identifier. Each sample has a “sample source”, the sample_source_identifier in the sample table should match one of the entries in the sample_source table. Essential columns here are; sample_source_identifier, sample_identifier, projects, group_name.

Then “extraction” information. This is for a specific RNA extraction from a sample. It’s identified as unique by a combination of sample id, and the date you did the extraction. The sample_identifier column here should match a sample_identifier column from the sample table. The extraction identifier column is only for if you do multiple extractions from the same sample on the same day, if you only do one sample on each date then this should always be `1`. Essential columns here are; sample_identifier, date_extracted, extraction_identifier, group_name, extraction_from. 

Then, finally (for the pre-bioinformatics section), the tiling PCR info. The sample identifier column here should match a sample_identifier column from the sample table, the date_extracted and extraction_identifier columns should match the information for that sample from the extraction table. Essential columns here are sample_identifier, date_extracted, extraction_identifier, 

I’ve attached a template for each sheet.

I know it’s quite a lot, so happy to meet to discuss or help out in any other way. The date extracted and date pcred columns don’t have to be “true”, they just have to consistent between the sheets (so if, in the extraction sheet you say you did the extraction on 01/06/2021, then on the tiling pcr sheet, you have to put that same date for that sample.


## old tests

Before running tests run `export DATABASE_URL="postgresql:///test_seqbox"`, and also run `conda activate seqbox`.



1. Nanopore, default, covid. Test 1 tests multiple things i) that the todo list query is working ok 
ii) end to end testing for covid workflow, nanopore default.

    a. `run_test_01.sh`

    b. uploads everything in `01.test_todo_list_query` dir
    
    c. run this query
    ```
    select sample.sample_identifier, sample.day_received, sample.month_received, sample.year_received, pr.pcr_result as qech_pcr_result, pr.ct as original_ct, project_name, e.extraction_identifier, DATE(e.date_extracted) as date_extracted, ccp.pcr_identifier, DATE(ccp.date_pcred) as date_covid_confirmatory_pcred,
    ccp.ct as covid_confirmation_pcr_ct, tp.pcr_identifier as tiling_pcr_identifier, DATE(tp.date_pcred) as date_tiling_pcrer, rsb.name as read_set_batch_name, r.readset_identifier
    from sample
    left join sample_source ss on sample.sample_source_id = ss.id
    left join sample_source_project ssp on ss.id = ssp.sample_source_id
    left join project on ssp.project_id = project.id
    left join pcr_result pr on sample.id = pr.sample_id
    left join extraction e on sample.id = e.sample_id
    left join covid_confirmatory_pcr ccp on e.id = ccp.extraction_id
    left join raw_sequencing rs on e.id = rs.extraction_id
    left join tiling_pcr tp on rs.tiling_pcr_id = tp.id
    left join raw_sequencing_batch rsb on rs.raw_sequencing_batch_id = rsb.id
    left join read_set r on rs.id = r.raw_sequencing_id
    order by sample.year_received desc, sample.month_received desc, sample.day_received desc
   ```
    Check that it gives this output:
    ```CMT15I,,,,Positive,15.4,COVIDseq,1,2021-06-01,1,2021-06-01,15.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,1
    CMT1XD,,,,Positive,15.4,COVIDseq,1,2021-06-01,1,2021-06-01,15.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,2
    CMT15J,,,,Positive,33.4,COVIDseq,1,2021-06-01,1,2021-06-01,33.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,3
    CMT15V,,,,Positive,22.5,COVIDseq,1,2021-06-01,1,2021-06-01,22.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,4
    CMT1KL,,,,Positive,38.5,COVIDseq,1,2021-06-01,1,2021-06-01,38.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,5
    CMT1KQ,,,,Positive,12.5,COVIDseq,1,2021-06-01,1,2021-06-01,12.5,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,6
    CMT16X,,,,Positive,12.4,COVIDseq,1,2021-06-01,1,2021-06-01,12.4,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,7
    CMT16E,,,,Positive,19.6,COVIDseq,1,2021-06-01,1,2021-06-01,19.6,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,8
    CMT15Q,,,,Negative,,COVIDseq,1,2021-06-01,1,2021-06-01,,1,2021-06-01,20201201_1355_MN33881_FAO20804_109641e0,9
    CPH121,,,,Positive,23.4,COVIDseq,1,2021-06-01,1,2021-06-01,23.4,,,,
    CMT163,,,,,,COVIDseq,1,2021-06-01,,,,,,,
    CMT16W,,,,,,COVIDseq,,,,,,,,,```
   
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

?. nanopore, default, covid. testing combined sample source, sample, covid confirmatory pcr, 
extraction, tiling pcr, readset.

8. illumina, extract is from cultures, not covid. testing a combined submission tracker input file with multiple samples.

9. illumina, extract is from sample.

10. test for combined submission tracker input file.

    a. run setup.sh - wipes/makes the db, adds the group and project.
 
    b. run upload_a.sh - adds sample sources, samples, and cultures.

    c. run upload_b.sh - adds extractions and elutions to the cultures from upload_a (models common lab flow)
    
    d. run upload_c.sh - adds sample sources, samples, extractions, and elutions from whole_sample
    
    e. run query_a.sh - gets the "to sequence" list

    f. run upload_d.sh - add sequencing information to the samples/extractions from upload_a/b
    
    g. run upload_e.sh - add sample sources, samples, cultures and extractions when the client submits extractions from culture (testing this logic, rather than submitting extractions from whole_sample or cultures)
 
11. test for submitting a sample in "dry" mode i.e. the sample isn't actually passed tp the sequencing service, we're just keeping track of it in the DB. and then at a later point it is submitted to the sequencing service.

12. test for submitting reads generated elsewhere.