set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_sample_sources -i test/01.test/submission_tracker.xlsx
python src/scripts/seqbox_cmd.py add_samples -i test/01.test/submission_tracker.xlsx
python src/scripts/seqbox_cmd.py add_pcr_results -i test/01.test/submission_tracker.xlsx
python src/scripts/seqbox_cmd.py add_extractions -i test/01.test/submission_tracker.xlsx
python src/scripts/seqbox_cmd.py add_tiling_pcrs -i test/01.test/submission_tracker.xlsx
python src/scripts/seqbox_cmd.py add_covid_confirmatory_pcrs -i test/01.test/submission_tracker.xlsx

python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/01.test/raw_sequencing_batch.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/01.test/readset_batches.csv
python src/scripts/seqbox_cmd.py add_readsets -i test/01.test/sequencing_tracker.xlsx -s -n
#python src/scripts/seqbox_filehandling.py add_readset_to_filestructure -i sequencing_tracker.xlsx -c test/test_seqbox_config.yaml -s -n
#python src/scripts/seqbox_cmd.py add_artic_covid_results -i test/01.test/artic_nf_covid_results.csv -b 20201201_1355_MN33881_FAO20804_109641e0 -w medaka -p docker
#python src/scripts/seqbox_cmd.py add_pangolin_results -i test/01.test/pangolin_results.csv -b 20201201_1355_MN33881_FAO20804_109641e0 -w medaka -p docker
