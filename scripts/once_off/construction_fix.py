#!/usr/bin/env python3
import re
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    for i in db:
        if (
            not i.meaning_1 and i.construction is not None and
            i.construction.startswith("a +")
        ):
            i.construction = re.sub(r"^a \+", "na > a +", i.construction)
            print(i.pali_1)
            print(i.construction)
            print(i.construction)
            print()

    db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
