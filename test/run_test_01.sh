set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python test/test_no_web.py # creates db
python src/scripts/seqbox_cmd.py add_groups -i test/01.test_todo_list_query/groups.csv
python src/scripts/seqbox_cmd.py add_projects -i test/01.test_todo_list_query/projects.csv
python src/scripts/seqbox_cmd.py add_pcr_assays -i test/templates/template_pcr_assay.csv 
python src/scripts/seqbox_cmd.py add_sample_sources -i test/01.test_todo_list_query/sample_sources.csv
python src/scripts/seqbox_cmd.py add_samples -i test/01.test_todo_list_query/samples.csv
python src/scripts/seqbox_cmd.py add_pcr_results -i test/01.test_todo_list_query/pcr_results.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/01.test_todo_list_query/extraction.csv
python src/scripts/seqbox_cmd.py add_tiling_pcrs -i test/01.test_todo_list_query/tiling_pcr.csv
python src/scripts/seqbox_cmd.py add_covid_confirmatory_pcrs -i test/01.test_todo_list_query/confirmatory_pcr.csv
python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/01.test_todo_list_query/raw_sequencing_batch.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/01.test_todo_list_query/readset_batches.csv
python src/scripts/seqbox_cmd.py add_readsets -i test/01.test_todo_list_query/nanopore_default_readsets.csv -c test/test_seqbox_config.yaml -s -n 