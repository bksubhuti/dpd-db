#!/usr/bin/env python3

"""Find synonyms and variants and add to database."""

import re
import pickle
import pyperclip

from rich import print
from rich.prompt import Prompt

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.db_search_string import db_search_string
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc

nouns = ["masc", "fem", "nt"]


def main():
    tic()
    print("[bright_yellow]finding synonyms and variants")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    exceptions = load_exceptions(pth)

    identical_meaning_dict = find_identical_meanings(dpd_db, exceptions)
    add_identical_meanings(pth, identical_meaning_dict, db_session, exceptions)

    single_meaning_dict = find_single_meanings(dpd_db, exceptions)
    dual_meanings_dict = find_dual_meanings(single_meaning_dict)
    add_dual_meanings(pth, dual_meanings_dict, db_session, exceptions)

    toc()


def load_exceptions(pth: ProjectPaths):
    """Load exceptions pickle file."""
    try:
        with open(pth.syn_var_exceptions_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []


def find_identical_meanings(dpd_db, exceptions):
    """Find words with the same pos and identical clean meanings."""
    print(f"[green]{'finding identical meanings'}", end=" ")

    identical_meaning_dict: dict = {}

    for __counter__, i in enumerate(dpd_db):
        if i.meaning_1:
            meaning = clean_meaning(i.meaning_1)

            if i.pos in nouns:
                pos_meaning = f"[noun] {meaning}"
            else:
                pos_meaning = f"[{i.pos}] {meaning}"

            if (
                i.pos != "pron" and
                i.pos != "sandhi" and
                meaning and
                pos_meaning not in exceptions and
                # no cases in grammar
                not re.findall(
                    r"\b(nom|acc|instr|dat|abl|gen|loc|voc)\b", i.grammar)
            ):
                if pos_meaning not in identical_meaning_dict:
                    identical_meaning_dict[pos_meaning] = [i.pali_1]
                else:
                    identical_meaning_dict[pos_meaning] += [i.pali_1]

    # remove single entries
    for k, v in identical_meaning_dict.copy().items():
        if len(v) < 2:
            del identical_meaning_dict[k]

    print(f"{len(identical_meaning_dict)}")
    return identical_meaning_dict


def clean_meaning(text):
    """Return text having removed
    1. commentary meaning,
    2. all brackets and their contents including
        proceeding or following spaces."""
    text = re.sub(r"\(comm\).*$", "", text)
    text = re.sub(r" \(.*?\) | \(.*?\)|\(.*?\) ", "", text)
    return text


def add_identical_meanings(pth: ProjectPaths, identical_meaning_dict, db_session, exceptions):
    """Process identical meanings and add to db."""
    print("[green]adding identical meanings to db")

    count = 0
    for meaning, headwords in identical_meaning_dict.items():
        if len(headwords) > 1:

            db = db_session.query(
                PaliWord).filter(PaliWord.pali_1.in_(headwords)).all()

            # sorted lists of clean headwords, synonyms and variants
            db = sorted(db, key=lambda x: pali_sort_key(x.pali_1))
            clean_headwords = pali_list_sorter([i.pali_clean for i in db])

            synonyms = pali_list_sorter(
                [syn for i in db for syn in i.synonym_list if syn])

            variants = pali_list_sorter(
                [var for i in db for var in i.variant_list if var])

            if (
                set(clean_headwords) != set(synonyms) and
                not set(clean_headwords).issubset(set(synonyms)) and
                set(clean_headwords) != set(variants) and
                not set(clean_headwords).issubset(set(variants))
            ):
                print(f"\n{count} / {len(identical_meaning_dict)}")

                for i in db:
                    print(f"[yellow]{i.pali_1:<20}[blue]{i.pos:10}[green]{i.meaning_1:<30} [cyan]{i.synonym_list} [violet]{i.variant_list}")
                print(f"[cyan]{synonyms}")
                print(f"[violet]{variants}")

                # the options are:
                # 1. add list of synomyms minus the headword
                # 2. add a list of variants minus the headword
                # 3. edit it manually if it's complicated
                # 4. add an exception
                # 5. pass
                # 6. break

                question = "[white](s)ynonym, (v)ariant, (m)anual (e)xception (p)ass (b)reak"
                choice = Prompt.ask(question)
                search_string = db_search_string(headwords)
                pyperclip.copy(search_string)

                if choice == "s":
                    for i in db:
                        synonyms = set(clean_headwords) | set(synonyms)
                        synonyms = synonyms - set([i.pali_clean])
                        synonyms = synonyms - set(i.variant_list)
                        synonyms = pali_list_sorter(synonyms)
                        i.synonym = ", ".join(synonyms)

                    print(search_string)
                    db_session.commit()

                elif choice == "v":
                    for i in db:
                        variants = set(clean_headwords) | set(variants)
                        variants = variants - set([i.pali_clean])
                        variants = variants - set(i.synonym_list)
                        variants = pali_list_sorter(variants)
                        i.variant = ", ".join(variants)

                    print(search_string)
                    db_session.commit()

                elif choice == "m":
                    print(search_string)
                    print(', '.join(clean_headwords))

                elif choice == "e":
                    exceptions += [meaning]
                    with open(pth.syn_var_exceptions_path, "wb") as f:
                        pickle.dump(exceptions, f)
                    print(exceptions)

                elif choice == "p":
                    continue

                elif choice == "b":
                    break

        count += 1


def find_single_meanings(dpd_db, exceptions):
    """Find words with the same pos and identical single meaning."""
    print(f"[green]{'finding single meanings'}", end=" ")

    # make a single_meanings_dict
    # iterate thru db
    # clean the meanings of brackets
    # split into a list
    # add each pos_meaning : headwords

    single_meanings_dict = {}

    for i in dpd_db:
        for meaning in i.meaning_1.split("; "):
            meaning = clean_meaning(meaning)
            if meaning:
                pos_meaning = f"{i.pos}:{meaning}"
                if (
                    i.pos != "pron" and
                    i.pos != "sandhi" and
                    pos_meaning not in exceptions and
                    # no cases in grammar
                    not re.findall(
                        r"\b(nom|acc|instr|dat|abl|gen|loc|voc|3rd|2nd|1st|reflx)\b", i.grammar)
                ):
                    if pos_meaning not in single_meanings_dict:
                        single_meanings_dict[pos_meaning] = set([i.pali_1])
                    else:
                        # dont include same headword with different numbers
                        if not re.findall(
                            fr"{i.pali_clean} \d.*",
                                ", ".join(single_meanings_dict[pos_meaning])):
                            single_meanings_dict[pos_meaning].add(i.pali_1)

    # remove meanings with single words
    # for (pos_meaning, word_list) in (single_meanings_dict.copy().items()):
    #     if len(word_list) < 2:
    #         del single_meanings_dict[pos_meaning]

    print(len(single_meanings_dict))
    assert ', ' not in single_meanings_dict
    return single_meanings_dict


def find_dual_meanings(single_meaning_dict):
    print("[green]Finding dual meanings")
    dual_meanings_dict = {}
    done_list = set()

    pos_meaning_items = list(single_meaning_dict.items())

    for counter, (pos_meaning1, word_list1) in enumerate(pos_meaning_items):
        pos1, meaning1 = pos_meaning1.split(":")

        for pos_meaning2, word_list2 in pos_meaning_items[counter+1:]:
            pos2, meaning2 = pos_meaning2.split(":")

            if pos1 == pos2 and meaning1 != meaning2:
                intersection = set(word_list1) & set(word_list2)
                if len(intersection) > 1:
                    tupled = tuple(intersection)
                    if tupled not in done_list:
                        pos_meanings = f"{pos1}:{meaning1}:{meaning2}"
                        dual_meanings_dict[pos_meanings] = intersection
                        done_list.add(tupled)

        if counter % 2500 == 0:
            print(f"{counter:>10} / {len(single_meaning_dict):<10}[green]{pos1:<10}[white]{meaning1}")

    print(len(dual_meanings_dict))
    return dual_meanings_dict


def add_dual_meanings(pth: ProjectPaths, dual_meanings_dict, db_session, exceptions):
    """Process dual meanings and add to db."""
    print("[green]adding dual meanings to db")

    break_flag = False

    for counter, (pos_meanings, word_list) in enumerate(
            dual_meanings_dict.items()):

        if break_flag is True:
            break

        pos, meaning1, meaning2 = pos_meanings.split(":")

        # go through each word_list and
        # add individual words to synonyms or variants

        db = db_session.query(
            PaliWord).filter(PaliWord.pali_1.in_(word_list)).all()

        # sorted lists of clean headwords, synonyms and variants
        db = sorted(db, key=lambda x: pali_sort_key(x.pali_1))
        clean_headwords = pali_list_sorter([i.pali_clean for i in db])

        synonyms = pali_list_sorter(
            set([syn for i in db for syn in i.synonym_list if syn]))

        variants = pali_list_sorter(
            set([var for i in db for var in i.variant_list if var]))

        if (
            set(clean_headwords) != set(synonyms) and
            not set(clean_headwords).issubset(set(synonyms)) and
            set(clean_headwords) != set(variants) and
            not set(clean_headwords).issubset(set(variants))
        ):
            print(f"\n{counter}. {pos}. {meaning1} / {meaning2}")

            for i in db:
                print(f"[yellow]{i.pali_1:<20}[blue]{i.pos:10}[green]{i.meaning_1:<30} [cyan]{i.synonym_list} [violet]{i.variant_list}")
            print(f"[cyan]{synonyms}")
            print(f"[violet]{variants}")

            # the options are:
            # 1. add list of synomyms minus the headword
            # 2. add a list of variants minus the headword
            # 3. edit it manually if it's complicated
            # 4. add an exception
            # 5. pass
            # 6. break

            question = "[white](s)ynonym, (v)ariant, (m)anual (e)xception (p)ass (b)reak"
            choice = Prompt.ask(question)
            search_string = db_search_string(word_list)
            pyperclip.copy(search_string)

            if choice == "s":
                for i in db:
                    synonyms = set(clean_headwords) | set(i.synonym_list)
                    synonyms = synonyms - set([i.pali_clean])
                    synonyms = synonyms - set(i.variant_list)
                    if "" in synonyms:
                        synonyms.remove("")
                    synonyms = pali_list_sorter(synonyms)
                    i.synonym = ", ".join(synonyms)

                print(search_string)
                db_session.commit()

            elif choice == "v":
                for i in db:
                    variants = set(clean_headwords) | set(i.variant_list)
                    variants = variants - set([i.pali_clean])
                    variants = variants - set(i.synonym_list)
                    if "" in variants:
                        variants.remove("")
                    variants = pali_list_sorter(variants)
                    i.variant = ", ".join(variants)

                print(search_string)
                db_session.commit()

            elif choice == "m":
                print(search_string)
                print(', '.join(clean_headwords))

            elif choice == "e":
                exceptions += [f"{pos_meanings}"]
                with open(pth.syn_var_exceptions_path, "wb") as f:
                    pickle.dump(exceptions, f)
                print(exceptions)

            elif choice == "p":
                continue

            elif choice == "b":
                break_flag = True
                break

        if counter % 100 == 0:
            print(f"{counter:>10} / {len(dual_meanings_dict):<10} {pos_meanings}")


if __name__ == "__main__":
    main()
