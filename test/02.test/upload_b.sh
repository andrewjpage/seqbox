set -e
set -o pipefail

# add the extraction info e.g. nucleic acid conc etc
python src/scripts/seqbox_cmd.py add_extractions -i test/02.test/submission_tracker_b.csv
# add the elution info e.g. elution plate id and elution plate well
python src/scripts/seqbox_cmd.py add_elution_info_to_extractions -i test/02.test/submission_tracker_b.csv
