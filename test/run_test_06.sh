set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python test/test_no_web.py # creates db
python src/scripts/seqbox_cmd.py add_groups -i test/06.test/groups.csv
python src/scripts/seqbox_cmd.py add_projects -i test/06.test/projects.csv
python src/scripts/seqbox_cmd.py add_sample_sources -i test/06.test/sample_sources.csv
python src/scripts/seqbox_cmd.py add_samples -i test/06.test/samples.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/06.test/extraction.csv
python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/06.test/raw_sequencing_batch.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/06.test/readset_batches.csv
python src/scripts/seqbox_cmd.py add_readsets -i test/06.test/nanopore_default_readsets.csv -n
python src/scripts/seqbox_filehandling.py add_readset_to_filestructure -i test/06.test/nanopore_default_readsets.csv -c test/test_seqbox_config.yaml -n
