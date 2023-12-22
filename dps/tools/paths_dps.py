"""All file paths that get used in the dps related codes."""

import os
from typing import Optional
from pathlib import Path

class DPSPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # csvs
        self.anki_csvs_dps_dir = base_dir.joinpath(Path("dps/csvs/anki_csvs/"))
        self.csv_dps_dir = base_dir.joinpath(Path("dps/csvs/"))
        self.dpd_dps_full_path = base_dir.joinpath(Path("dps/csvs/dpd_dps_full.csv"))
        self.dps_full_path = base_dir.joinpath(Path("dps/csvs/dps_full.csv"))
        self.dps_csv_path = base_dir.joinpath(Path("dps/csvs/dps.csv"))
        self.sbs_index_path = base_dir.joinpath(Path("dps/sbs_index.csv"))
        self.class_index_path = base_dir.joinpath(Path("dps/csvs/class_index.csv"))
        self.sutta_index_path = base_dir.joinpath(Path("dps/csvs/sutta_index.csv"))
        self.freq_ebt_path = base_dir.joinpath(Path("dps/csvs/freq_ebt.csv"))
        self.dpd_dps_full_freq_path = base_dir.joinpath(Path("dps/csvs/dpd_dps_full_freq.csv"))
        self.ai_ru_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_ru_suggestion_history.csv"))
        self.ai_ru_notes_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_ru_notes_suggestion_history.csv"))
        self.ai_en_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_en_suggestion_history.csv"))
        self.temp_csv_path = base_dir.joinpath(Path("dps/csvs/temp.csv"))
        self.id_to_add_path = base_dir.joinpath(Path("dps/csvs/id_to_add.csv"))
        self.id_temp_list_path = base_dir.joinpath(Path("dps/csvs/id_temp_list.csv"))

        self.sbs_pd_path = base_dir.joinpath(Path("dps/csvs/sbs_pd.csv"))

        # /tests
        self.dps_internal_tests_path = base_dir.joinpath(Path("dps/csvs/dps_internal_tests.tsv"))
        self.dps_internal_tests_replaced_path = base_dir.joinpath(Path("dps/csvs/dps_internal_tests_replaced.tsv"))
        self.dps_test_1_path = base_dir.joinpath(Path("dps/csvs/dps_test_1.tsv"))
        self.dps_test_2_path = base_dir.joinpath(Path("dps/csvs/dps_test_2.tsv"))

        # spreadsheets
        self.dps_path = base_dir.joinpath(Path("dps/dps.ods"))

        # dps bakup folder
        self.dps_backup_dir = base_dir.joinpath(Path("dps/backup/")) 
        self.for_compare_dir = base_dir.joinpath(Path("dps/backup/for_compare/")) 
        self.temp_csv_backup_dir = base_dir.joinpath(Path("dps/csvs/backup_csv/")) 

        # db with frequency
        self.freq_db_path = base_dir.joinpath(Path("dps/freq.db"))

        # txt
        self.ru_user_dict_path = base_dir.joinpath(Path("dps/tools/ru_user_dictionary.txt"))
        self.text_to_add_path = base_dir.joinpath(Path("temp/text.txt"))
        self.dpd_dps_concise_txt_path = base_dir.joinpath(Path("temp/dpd_dps_concise.txt"))

        # /gui/stash
        self.dps_stash_path = base_dir.joinpath(Path("gui/stash/dps_stash.json"))

        # .. external
        self.sbs_anki_style_dir = base_dir.joinpath(Path("../sasanarakkha/study-tools/anki-style/"))
        self.local_downloads_dir = base_dir.joinpath(Path("../../Downloads/"))
        self.anki_media_dir = base_dir.joinpath(Path("/home/deva/.var/app/net.ankiweb.Anki/data/Anki2/deva/collection.media/")) 

        if create_dirs:
            self.create_dirs()


    def create_dirs(self):
            for d in [
                self.anki_csvs_dps_dir,
                self.csv_dps_dir,
                self.dps_backup_dir,
                self.for_compare_dir,
                self.temp_csv_backup_dir,
            ]:
                d.mkdir(parents=True, exist_ok=True)

