# !/usr/bin/env python3
# coding: utf-8

import re
import pickle

from pathlib import Path
from dpd.models import PaliWord, PaliRoot
from dpd.db_helpers import get_db_session

dpd_db_path = Path("dpd.sqlite3")
db_session = get_db_session(dpd_db_path)

pos_list = ['abbrev', 'abs', 'adj', 'aor', 'card', 'cond', 'cs', 'fem', 'fut', 'ger', 'idiom', 'imp', 'imperf', 'ind', 'inf', 'letter', 'masc', 'nt', 'opt', 'ordin', 'perf', 'pp', 'pr', 'prefix', 'pron', 'prp', 'ptp', 'root', 'sandhi', 'suffix', 'var', 've']


def family_root_contains_plus():
    print(f"family root contains plus")

    filtered_db = db_session.query(PaliWord).filter(PaliWord.family_root.contains("+")).all()

    for i in filtered_db:
        i.family_root = re.sub(r" \+ ", " ", str(i.family_root))
        db_session.commit()


def family_compound_contains_plus():
    print(f"family compound contains plus")
    filtered_db = db_session.query(PaliWord).filter(
        PaliWord.family_compound.contains("+")).all()

    for i in filtered_db:
        i.family_compound = re.sub(r" \+ ", " ", str(i.family_compound))
        db_session.commit()


def family_root_missing():
    print(f"family root missing")
    filtered_db = db_session.query(PaliWord).filter(
        PaliWord.family_root == None,
        PaliWord.root_key != None
    ).all()

    if len(filtered_db) > 0:
        print(f"family_root missing ")
        for i in filtered_db:
            print(f"\t{i}")
            input()
            family_root_missing()


def problem_patterns():
    print(f"problem patterns")
    with open("../inflection generator/output/inflection tables dict", "rb") as p:
        inflection_tables_dict = pickle.load(p)
    patterns = inflection_tables_dict.keys()

    filtered_db = db_session.query(PaliWord).filter(
        PaliWord.pattern != None,
        PaliWord.pattern.notin_(patterns)
        ).all()

    if len(filtered_db) > 0:
        for i in filtered_db:
            print(f"\t{i.id} {i.pali_1} {i.pattern}")
        input()
        problem_patterns()


def wrong_pos():
    print(f"wrong pos")

    filtered_db = db_session.query(PaliWord).filter(PaliWord.pos.notin_(pos_list)).all()
    if len(filtered_db) > 0:
        for i in filtered_db:
            print(f"\t{i.id} {i.pali_1} {i.pos}")
        input()
        wrong_pos()


def main():
    family_root_contains_plus()
    family_compound_contains_plus()
    family_root_missing()
    problem_patterns()
    wrong_pos()
    # test for pos ≠ pattern
    # <br> in family 2
    # missing abbreviations in help file
    # test_for_errors_in_sandhi_manual_correct


if __name__ == "__main__":
    main()
