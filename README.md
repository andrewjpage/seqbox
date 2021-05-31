# seqbox
local sequence management lightweight tools

## Database notes

* sample_source_identifier needs to be unique within a group
* if you add an existing sample_source_identifier associated with a different 
project then that sample_source_identifier will be associated
with that project.
* projects can't be shared between groups
* projects is an attribute of sample_source because it's the 
sample source which is the primary thing enrolled in the project,
not the sample itself