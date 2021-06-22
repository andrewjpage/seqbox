set -e
set -o pipefail

python scripts/seqbox_cmd.py add_sample_sources -i scripts/proper_test/covid_sample_sources_2.csv
python scripts/seqbox_cmd.py add_samples -i scripts/proper_test/covid_samples_example_2.csv
python scripts/seqbox_cmd.py add_extractions -i scripts/proper_test/covid_extraction_2.csv
python scripts/seqbox_cmd.py add_tiling_pcrs -i scripts/proper_test/covid_tiling_pcr_2.csv
python scripts/seqbox_cmd.py add_covid_confirmatory_pcr -i scripts/proper_test/covid_confirmatory_pcr_2.csv
python scripts/seqbox_cmd.py add_readsets -i scripts/proper_test/covid_nanopore_readsets_2.csv -c scripts/test_seqbox_config.yaml 
