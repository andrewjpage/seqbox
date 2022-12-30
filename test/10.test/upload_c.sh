set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_sample_sources -i test/10.test/submission_tracker_c.csv
python src/scripts/seqbox_cmd.py add_samples -i test/10.test/submission_tracker_c.csv
python src/scripts/seqbox_cmd.py add_extractions -i test/10.test/submission_tracker_c.csv
python src/scripts/seqbox_cmd.py add_elution_info_to_extractions -i test/10.test/submission_tracker_c.csv
