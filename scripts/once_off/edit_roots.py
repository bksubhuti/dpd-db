from db.get_db_session import get_db_session
from db.models import PaliRoot
from tools.paths import ProjectPaths

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
roots_db = db_session.query(PaliRoot).all()

for i in roots_db:
    if i.root == "√pā":
        i.root = "√pā 2"

db_session.commit()
db_session.close()
