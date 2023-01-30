set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_cultures -i test/03.test/submission_tracker_b.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/03.test/submission_tracker_b.csv
