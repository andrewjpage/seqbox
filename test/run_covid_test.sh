set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python scripts/test_no_web.py # creates db
python scripts/seqbox_cmd.py add_groups -i scripts/groups_example.csv
python scripts/seqbox_cmd.py add_projects -i scripts/projects_example.csv
python scripts/seqbox_cmd.py add_sample_sources -i scripts/proper_test/covid_sample_sources.csv
python scripts/seqbox_cmd.py add_samples -i scripts/proper_test/covid_samples_example.csv
python scripts/seqbox_cmd.py add_extractions -i scripts/proper_test/covid_extraction.csv
python scripts/seqbox_cmd.py add_tiling_pcrs -i scripts/proper_test/covid_tiling_pcr.csv
python scripts/seqbox_cmd.py add_covid_confirmatory_pcr -i scripts/proper_test/covid_confirmatory_pcr.csv
python scripts/seqbox_cmd.py add_raw_sequencing_batches -i scripts/proper_test/covid_raw_sequencing_batch_updated.csv
python scripts/seqbox_cmd.py add_readsets -i scripts/proper_test/covid_nanopore_readsets_updated.csv -c scripts/test_seqbox_config.yaml -s -n 

