set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_sample_sources -i test/04.test/external_submission.csv
python src/scripts/seqbox_cmd.py add_samples -i test/04.test/external_submission.csv
python src/scripts/seqbox_cmd.py add_cultures -i test/04.test/external_submission.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/04.test/external_submission.csv
python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/02.test/raw_sequencing_batch.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/02.test/readset_batches.csv
python src/scripts/seqbox_cmd.py add_readsets -i test/04.test/external_submission.csv