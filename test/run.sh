set -e
set -o pipefail

rm app/pa_seqbox_v2_test.db
python scripts/test_no_web.py # creates db
python scripts/seqbox_cmd.py add_groups -i scripts/groups_example.csv
python scripts/seqbox_cmd.py add_projects -i scripts/projects_example.csv
python scripts/seqbox_cmd.py add_sample_sources -i scripts/sample_sources_example.csv
python scripts/seqbox_cmd.py add_samples -i scripts/samples_example.csv
python scripts/seqbox_cmd.py add_extractions -i scripts/extraction_example.csv
python scripts/seqbox_cmd.py add_tiling_pcrs -i scripts/tiling_pcr_example.csv
python scripts/seqbox_cmd.py add_raw_sequencing_batches -i scripts/raw_sequencing_batch_example.csv
python scripts/seqbox_cmd.py add_readsets -i scripts/nanopore_read_sets_example.csv -c scripts/test_seqbox_config.yaml 
python scripts/seqbox_cmd.py add_readsets -i scripts/illumina_read_sets_example.csv -c scripts/test_seqbox_config.yaml
python scripts/seqbox_cmd.py add_covid_readsets -i scripts/covid_nanopore_read_sets_example.csv -c scripts/test_seqbox_config.yaml
