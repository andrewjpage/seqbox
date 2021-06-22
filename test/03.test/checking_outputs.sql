
# should be at least two projects (pseudo seq and acineto seq) belonging to Core
select * from groups
join project p on groups.id = p.groups_id;



# PTS15G should be in both pseudo seq and acineto seq
select * from sample_source
join sample_source_project ssp on sample_source.id = ssp.sample_source_id
join project p on ssp.project_id = p.id
where project_name = any(array['PseudomonasSeq', 'AcinetobacterSeq'])

# should be multiple samples for sample source ABS15V and PTS89D
select sample_identifier, sample_source_identifier, project_name from sample
join sample_source ss on sample.sample_source_id = ss.id
join sample_source_project ssp on ss.id = ssp.sample_source_id
join project p on ssp.project_id = p.id
where project_name = any(array['PseudomonasSeq', 'AcinetobacterSeq']);