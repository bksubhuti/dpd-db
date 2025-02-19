import csv
from pathlib import Path
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

PTH = ProjectPaths()
db_session = get_db_session(PTH.dpd_db_path)

db = db_session.query(PaliWord).all()

old_dpd_csv_path = Path("../csvs/dpd-full.csv")

with open(old_dpd_csv_path, newline="") as csvfile:
    reader = csv.DictReader(csvfile, delimiter="\t")
    old_dpd = [row for row in reader]


origin_dict = {}
for i in old_dpd:
    if i["Origin"]:
        id = i["ID"]
        origin = i["Origin"]
        pali_1 = i["Pāli1"]
        origin_dict[id] = (pali_1, origin)

print(origin_dict, len(origin_dict))

for i in db:
    user_id = str(i.user_id)
    if user_id in origin_dict:
        origin = origin_dict[user_id][1]
        i.origin = origin

db_session.commit()
db_session.close()
