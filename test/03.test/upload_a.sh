set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_sample_sources -i test/03.test/submission_tracker_a.csv
python src/scripts/seqbox_cmd.py add_samples -i test/03.test/submission_tracker_a.csv -d
