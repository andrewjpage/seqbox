set -e
set -o pipefail

#rm app/pa_seqbox_v2_test.db
python ../test_no_web.py # creates db
python ../../src/scripts/seqbox_cmd.py add_groups -i ../10.test/groups.csv
python ../../src/scripts/seqbox_cmd.py add_projects -i ../10.test/projects.csv