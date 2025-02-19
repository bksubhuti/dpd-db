#!/usr/bin/env python3

"""Create an html table of all words belonging to the same family."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyWord

from tools.meaning_construction import clean_construction
from tools.meaning_construction import degree_of_completion
from tools.meaning_construction import make_meaning
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.superscripter import superscripter_uni
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day


def main():
    tic()

    print("[bright_yellow]word families generator")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    wf_db = db_session.query(
        PaliWord).filter(PaliWord.family_word != "").all()
    wf_db = sorted(wf_db, key=lambda x: pali_sort_key(x.pali_1))

    wf_dict = make_word_fam_dict(wf_db)
    wf_dict = compile_wf_html(wf_db, wf_dict)
    errors_list = add_wf_to_db(db_session, wf_dict)
    print_errors_list(errors_list)
    anki_exporter(pth, wf_dict)
    toc()


def make_word_fam_dict(wf_db):
    print("[green]extracting word families", end=" ")

    # create a dict of all word families
    # word: {headwords: [], html: "", }

    wf_dict: dict = {}

    for __counter__, i in enumerate(wf_db):
        wf = i.family_word

        if " " in wf:
            print("[bright_red]ERROR: spaces found please remove!")

        if wf in wf_dict:
            wf_dict[wf]["headwords"] += [i.pali_1]
        else:
            wf_dict[wf] = {
                "headwords": [i.pali_1],
                "html": "",
                "data": []}

    print(len(wf_dict))
    return wf_dict


def compile_wf_html(wf_db, wf_dict):
    print("[green]compiling html")

    for __counter__, i in enumerate(wf_db):
        wf = i.family_word
        if i.pali_1 in wf_dict[wf]["headwords"]:
            if not wf_dict[wf]["html"]:
                html_string = "<table class='family'>"
            else:
                html_string = wf_dict[wf]["html"]

            meaning = make_meaning(i)
            html_string += "<tr>"
            html_string += f"<th>{superscripter_uni(i.pali_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{meaning} {degree_of_completion(i)}</td>"
            html_string += "</tr>"

            wf_dict[wf]["html"] = html_string

            # anki data
            construction = clean_construction(
                i.construction) if i.meaning_1 else ""
            wf_dict[wf]["data"] += [
                (i.pali_1, i.pos, meaning, construction)]

    for i in wf_dict:
        wf_dict[i]["html"] += "</table>"

    return wf_dict


def add_wf_to_db(db_session, wf_dict):
    print("[green]adding to db", end=" ")

    add_to_db = []
    errors_list = []

    for __counter__, wf in enumerate(wf_dict):
        if len(wf_dict[wf]["headwords"]) < 2:
            errors_list += [wf]

        wf_data = FamilyWord(
            word_family=wf,
            html=wf_dict[wf]["html"],
            count=len(wf_dict[wf]["headwords"]))
        add_to_db.append(wf_data)

    db_session.execute(FamilyWord.__table__.delete()) # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print("[white]ok")

    return errors_list


def print_errors_list(errors_list):
    if len(errors_list) > 0:
        print("[bright_red]ERROR: only 1 word in family:", end=" ")
    for error in errors_list:
        print(f"{error}", end=" ")
    print()


def anki_exporter(pth: ProjectPaths, wf_dict):
    """Save to TSV for anki."""
    print("[green]saving tsv for anki")
    anki_data_list = []
    for i in wf_dict:
        html = "<table><tbody>"
        for row in wf_dict[i]["data"]:
            headword, pos, meaning, construction = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{construction}</div></td></tr>"

        html += "</tbody></table>"
        if len(html) > 131072:
            print(f"[red]{i} longer than 131072 characters")
        else:
            anki_data_list += [(i, html, day())]

    file_path = pth.family_word_tsv_path
    header = []
    write_tsv_list(str(file_path), header, anki_data_list)


if __name__ == "__main__":
    main()
