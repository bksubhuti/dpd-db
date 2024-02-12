#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    for counter, i in enumerate(db):
        print(counter, i.lemma_1)


if __name__ == "__main__":
    main()
