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
where species = 'SARS-CoV-2' and pr.pcr_result like 'Positive%' and project_name = any(array['ISARIC'])
order by e.date_extracted desc, ccp.date_pcred desc, tp.date_pcred desc, rsb.name desc, r.readset_identifier desc;

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
join sample s on e.sample_id = s.id

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