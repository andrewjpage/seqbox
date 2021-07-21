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
