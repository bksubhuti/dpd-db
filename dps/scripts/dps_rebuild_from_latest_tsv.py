#!/usr/bin/env python3

"""Rebuild the databse from scratch from latest files in dps/backup folder. Modfied copy of https://github.com/digitalpalidictionary/dpd-db/blob/main/scripts/db_rebuild_from_tsv.py"""

import csv
import os

from rich.console import Console

from db.get_db_session import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import PaliWord, PaliRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths as DPSPTH

console = Console()


def get_latest_backup(prefix):
    """Get the latest backup file from a given directory with a specific prefix."""
    backup_files = [f for f in os.listdir(DPSPTH.dps_backup_dir) if f.startswith(prefix)]
    return os.path.join(DPSPTH.dps_backup_dir, sorted(backup_files, reverse=True)[0])



def main():
    tic()
    console.print("[bold bright_yellow]rebuilding db from dps/backup/*.tsvs")

    pth = ProjectPaths()
    if pth.dpd_db_path.exists():
        pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    db_session = get_db_session(pth.dpd_db_path)

    pali_word_latest_tsv = get_latest_backup("paliword")
    pali_root_latest_tsv = get_latest_backup("paliroot")
    russian_latest_tsv = get_latest_backup("russian")
    sbs_latest_tsv = get_latest_backup("sbs")

    make_pali_word_table_data(db_session, pali_word_latest_tsv)
    make_pali_root_table_data(db_session, pali_root_latest_tsv)
    make_russian_table_data(db_session, russian_latest_tsv)
    make_sbs_table_data(db_session, sbs_latest_tsv)



    db_session.commit()
    db_session.close()
    console.print("[bold bright_green]database restored successfully")
    toc()


def make_pali_word_table_data(db_session, pali_word_latest_tsv):
    """Read TSV and return PaliWord table data."""
    console.print("[bold green]creating PaliWord table data")
    with open(pali_word_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(PaliWord(**data))


def make_pali_root_table_data(db_session, pali_root_latest_tsv):
    """Read TSV and return PaliRoot table data."""
    console.print("[bold green]creating PaliRoot table data")
    with open(pali_root_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in (
                    "created_at", "updated_at",
                        "root_info", "root_matrix"):
                    data[col_name] = value
            db_session.add(PaliRoot(**data))


def make_russian_table_data(db_session, russian_latest_tsv):
    """Read TSV and return Russian table data."""
    console.print("[bold green]creating Russian table data")
    with open(russian_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))


def make_sbs_table_data(db_session, sbs_latest_tsv):
    """Read TSV and return SBS table data."""
    console.print("[bold green]creating SBS table data")
    with open(sbs_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))


if __name__ == "__main__":
    main()
