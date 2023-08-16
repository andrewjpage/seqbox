set -e
set -o pipefail

python src/scripts/seqbox_cmd.py add_groups -i test/01.test/groups.csv
python test/test_no_web.py # creates db
python src/scripts/seqbox_cmd.py add_projects -i test/01.test/projects.csv
python src/scripts/seqbox_cmd.py add_pcr_assays -i test/01.test/pcr_assay.csv