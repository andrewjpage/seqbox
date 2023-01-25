set -e
set -o pipefail

python ../../src/scripts/seqbox_cmd.py add_sample_sources -i ../10.test/submission_tracker_a.csv
python ../../src/scripts/seqbox_cmd.py add_samples -i ../10.test/submission_tracker_a.csv
python ../../src/scripts/seqbox_cmd.py add_cultures -i ../10.test/submission_tracker_a.csv
