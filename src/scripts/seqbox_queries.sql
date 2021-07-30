-- get covid todo list

select sample.sample_identifier, sample.day_received, sample.month_received, sample.year_received, pr.pcr_result as qech_pcr_result, project_name, e.extraction_identifier, DATE(e.date_extracted) as date_extracted, ccp.pcr_identifier, DATE(ccp.date_pcred) as date_covid_confirmatory_pcred,
       ccp.ct as covid_confirmation_pcr_ct, tp.pcr_identifier as tiling_pcr_identifier, DATE(tp.date_pcred) as date_tiling_pcrer, rsb.name as read_set_batch_name, r.readset_identifier
from sample
left join sample_source ss on sample.sample_source_id = ss.id
left join sample_source_project ssp on ss.id = ssp.sample_source_id
left join project on ssp.project_id = project.id
left join pcr_result pr on sample.id = pr.sample_id
left join extraction e on sample.id = e.sample_id
left join covid_confirmatory_pcr ccp on e.id = ccp.extraction_id
left join tiling_pcr tp on e.id = tp.extraction_id
left join raw_sequencing rs on e.id = rs.extraction_id
left join raw_sequencing_batch rsb on rs.raw_sequencing_batch_id = rsb.id
left join read_set r on rs.id = r.raw_sequencing_id
where species = 'SARS-CoV-2' and pr.pcr_result like 'Positive%' and project_name = any(array['ISARIC', 'COCOA'])
order by sample.year_received desc, sample.month_received desc, sample.day_received;

-- get pangolin results for plotting

select readset_identifier, sample_identifier, lineage, day_received, month_received, year_received from pangolin_result
join artic_covid_result acr on pangolin_result.artic_covid_result_id = acr.id
join read_set rs on rs.id = acr.readset_id
join raw_sequencing r on rs.raw_sequencing_id = r.id
join extraction e on r.extraction_id = e.id
join sample s on e.sample_id = s.id
where lineage != 'None';

-- get artic qc and pangolin results

select readset_identifier, sample_identifier, pct_covered_bases, lineage, day_received, month_received, year_received from pangolin_result
join artic_covid_result acr on pangolin_result.artic_covid_result_id = acr.id
join read_set rs on rs.id = acr.readset_id
join raw_sequencing r on rs.raw_sequencing_id = r.id
join extraction e on r.extraction_id = e.id
join sample s on e.sample_id = s.id;

-- get readset batch, readset id, sample id

select name, readset_identifier, sample_identifier from read_set
join read_set_batch on read_set.readset_batch_id = read_set_batch.id
join raw_sequencing rs on read_set.raw_sequencing_id = rs.id
join extraction e on rs.extraction_id = e.id
join sample s on e.sample_id = s.id

-- get all the samples from a run

select readset_identifier, sample_identifier, barcode, name from read_set
join read_set_nanopore rsn on read_set.id = rsn.readset_id
join read_set_batch rsb on read_set.readset_batch_id = rsb.id
join raw_sequencing rs on read_set.raw_sequencing_id = rs.id
join extraction e on rs.extraction_id = e.id
join sample s on e.sample_id = s.id
where name = '20210713_1422_MN33881_FAO36609_d9ac6fbd';

-- get all info on sample, need to add some more info to this and rename column headings

select group_name, project_name, sample_source_identifier, sample_identifier, pr.pcr_result, e.date_extracted,  ccp.ct, tp.date_pcred, tp.protocol, readset_identifier, name from sample
join pcr_result pr on sample.id = pr.sample_id
join extraction e on sample.id = e.sample_id
join covid_confirmatory_pcr ccp on e.id = ccp.extraction_id
join tiling_pcr tp on e.id = tp.extraction_id
join raw_sequencing rs on e.id = rs.extraction_id
join read_set r on rs.id = r.raw_sequencing_id
join read_set_batch rsb on r.readset_batch_id = rsb.id
join sample_source ss on sample.sample_source_id = ss.id
join sample_source_project ssp on ss.id = ssp.sample_source_id
join project p on ssp.project_id = p.id
join groups g on p.groups_id = g.id
where sample_identifier = 'CMT22M'
;

-- change the project associated with the originating sample sources for all samples with CMU sample identifier
--  warning - this won't handle sample sources which belong to multiple projects well. need to add another
--  check about is project.id = 'X' where switching from a specific project to another. e.g. ISARIC to DHO COVID

update sample_source_project set project_id = 3
from sample_source, sample
where sample.sample_identifier like 'CMU%'
and sample_source_project.sample_source_id = sample_source.id
and sample_source.id = sample.sample_source_id;

-- AAP report, distinct samples sequenced, which arent super script, aren't on duplicated runs, etc.

select distinct on(sample_identifier) readset_identifier, sample_identifier, pct_covered_bases, project_name, barcode, rsb.name
from read_set
left join read_set_nanopore on read_set.id = read_set_nanopore.readset_id
left join artic_covid_result on read_set.id = artic_covid_result.readset_id
left join raw_sequencing rs on read_set.raw_sequencing_id = rs.id
left join raw_sequencing_batch rsb on rs.raw_sequencing_batch_id = rsb.id
left join extraction e on rs.extraction_id = e.id
left join tiling_pcr on e.id = tiling_pcr.extraction_id
left join sample s on e.sample_id = s.id
left join sample_source ss on s.sample_source_id = ss.id
left join sample_source_project ssp on ss.id = ssp.sample_source_id
left join project p on ssp.project_id = p.id
where not rsb.name = any(array['20210623_1513_MN33881_FAO36636_d6fbf869', '20210628_1538_MN33881_FAO36636_219737d0'])
and tiling_pcr.protocol not like '%SuperScript%' or tiling_pcr.protocol is Null
and project_name = any(array['ISARIC', 'COCOA'])
and sample_identifier != 'Neg ex'
order by sample_identifier, pct_covered_bases desc;

-- AAP sql query, number with more than 80% coverage
-- from here https://www.cybertec-postgresql.com/en/postgresql-group-by-expression/
select project_name, count(project_name), pct_covered_bases >= 80 from (
select distinct on (sample_identifier) readset_identifier, sample_identifier, pct_covered_bases, project_name, barcode
from read_set
left join read_set_nanopore on read_set.id = read_set_nanopore.readset_id
left join artic_covid_result on read_set.id = artic_covid_result.readset_id
left join raw_sequencing rs on read_set.raw_sequencing_id = rs.id
left join extraction e on rs.extraction_id = e.id
left join tiling_pcr on e.id = tiling_pcr.extraction_id
left join sample s on e.sample_id = s.id
left join sample_source ss on s.sample_source_id = ss.id
left join sample_source_project ssp on ss.id = ssp.sample_source_id
left join project p on ssp.project_id = p.id
where pct_covered_bases is not Null
and project_name = any(array['ISARIC', 'COCOA'])
and sample_identifier != 'Neg ex'
and (year_received >= 2021 and month_received >= 6)
and (tiling_pcr.protocol not like '%SuperScript%' or tiling_pcr.protocol is Null)
order by sample_identifier, pct_covered_bases desc) as foo
group by project_name, pct_covered_bases >= 80;

-- AAP report, numnber of samples received and pcr positive/negative

select project_name, count(project_name), pcr_result, count(pcr_result) from (
    select distinct on (sample_identifier) split_part(pcr_result, ' -', 1) as pcr_result, project_name from sample
    join pcr_result pr on sample.id = pr.sample_id
    join sample_source ss on sample.sample_source_id = ss.id
    join sample_source_project ssp on ss.id = ssp.sample_source_id
    join project p on ssp.project_id = p.id
    where (year_received >= 2021 and month_received >= 6)
    and project_name = any(array['COCOA', 'COCOSU', 'ISARIC'])
    and pcr_result != 'Not Done') as foo
group by project_name, pcr_result;

-- AAP report, number of each lineage

select lineage, count(lineage) from (
select distinct on (sample_identifier) lineage
from read_set
left join read_set_nanopore on read_set.id = read_set_nanopore.readset_id
left join artic_covid_result on read_set.id = artic_covid_result.readset_id
left join pangolin_result on artic_covid_result.id = pangolin_result.artic_covid_result_id
left join raw_sequencing rs on read_set.raw_sequencing_id = rs.id
left join extraction e on rs.extraction_id = e.id
left join tiling_pcr on e.id = tiling_pcr.extraction_id
left join sample s on e.sample_id = s.id
left join sample_source ss on s.sample_source_id = ss.id
left join sample_source_project ssp on ss.id = ssp.sample_source_id
left join project p on ssp.project_id = p.id
where pct_covered_bases is not Null
and project_name = any(array['ISARIC', 'COCOA'])
and sample_identifier != 'Neg ex'
and (year_received >= 2021 and month_received >= 6)
and (tiling_pcr.protocol not like '%SuperScript%' or tiling_pcr.protocol is Null)
order by sample_identifier, pct_covered_bases desc) as foo
group by lineage