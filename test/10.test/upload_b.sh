set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_extractions -i test/10.test/submission_tracker_b.csv
python src/scripts/seqbox_cmd.py add_elution_info_to_extractions -i test/10.test/submission_tracker_b.csv
