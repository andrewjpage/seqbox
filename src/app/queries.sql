

select i.id, i.isolate_identifier,
       rs.id, rs.isolate_id, rs.read_set_filename,
       irs.id, irs.read_set_id, irs.path_r1, irs.path_r1
from isolate i
left join read_set rs on i.id = rs.isolate_id
left join illumina_read_set irs on irs.read_set_id = rs.id;
