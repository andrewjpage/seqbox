set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python test/test_no_web.py # creates db
python src/scripts/seqbox_cmd.py add_groups -i test/10.test/groups.csv
python src/scripts/seqbox_cmd.py add_projects -i test/10.test/projects.csv

