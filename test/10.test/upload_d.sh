set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_raw_sequencing_batches -i test/10.test/raw_sequencing_batch.csv
python src/scripts/seqbox_cmd.py add_readset_batches -i test/10.test/readset_batches.csv
python src/scripts/seqbox_cmd.py add_readsets -i test/10.test/sequencing_run.csv
python src/scripts/seqbox_cmd.py add_mykrobes -i test/10.test/mykrobe.csv