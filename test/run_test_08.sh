set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python test/test_no_web.py # creates db
python src/scripts/seqbox_cmd.py add_groups -i test/08.test/groups.csv
python src/scripts/seqbox_cmd.py add_projects -i test/08.test/projects.csv
python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/08.test/raw_sequencing_batches.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/08.test/readset_batches.csv
python src/scripts/seqbox_cmd.py add_pcr_assays -i test/08.test/pcr_assay.csv 


python src/scripts/seqbox_cmd.py add_sample_sources -i test/08.test/combined.csv
python src/scripts/seqbox_cmd.py add_samples -i test/08.test/combined.csv
python src/scripts/seqbox_cmd.py add_pcr_results -i test/08.test/combined.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/08.test/combined.csv
python src/scripts/seqbox_cmd.py add_covid_confirmatory_pcrs -i test/08.test/combined.csv
python src/scripts/seqbox_cmd.py add_tiling_pcrs -i test/08.test/combined.csv

python src/scripts/seqbox_cmd.py add_readsets -i test/08.test/combined.csv -s -n
python src/scripts/seqbox_filehandling.py add_readset_to_filestructure -i test/08.test/combined.csv -c test/test_seqbox_config.yaml -s -n

