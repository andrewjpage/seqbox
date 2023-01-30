set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_sample_sources -i test/02.test/submission_tracker_a.csv
python src/scripts/seqbox_cmd.py add_samples -i test/02.test/submission_tracker_a.csv
python src/scripts/seqbox_cmd.py add_cultures -i test/02.test/submission_tracker_a.csv
