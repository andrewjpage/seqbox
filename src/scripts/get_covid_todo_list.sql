select sample.sample_identifier, e.extraction_identifier, DATE(e.date_extracted), ccp.pcr_identifier, DATE(ccp.date_pcred),
       ccp.ct, tp.pcr_identifier, DATE(tp.date_pcred), rsb.name, r.readset_identifier
from sample
left join extraction e on sample.id = e.sample_id
left join covid_confirmatory_pcr ccp on e.id = ccp.extraction_id
left join tiling_pcr tp on e.id = tp.extraction_id
left join raw_sequencing rs on e.id = rs.extraction_id
left join raw_sequencing_batch rsb on rs.raw_sequencing_batch_id = rsb.id
left join read_set r on rs.id = r.raw_sequencing_id
where species = 'SARS-CoV-2'
order by e.date_extracted desc, ccp.date_pcred desc, tp.date_pcred desc, rsb.name desc, r.readset_identifier desc;
