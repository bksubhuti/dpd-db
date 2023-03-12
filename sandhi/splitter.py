#!/usr/bin/env python3.10

import pickle
import re
import pandas as pd
import cProfile

from rich import print
from typing import List
from os import popen
from copy import copy

from tools.pali_alphabet import vowels
from tools.timeis import tic, toc, bip, bop
from helpers import ResourcePaths, get_resource_paths


class Word:
    count_value: int = 0

    def __init__(self, word: str):
        Word.count_value += 1
        self.count = Word.count_value
        self.word: str = word
        self.tried: List = set()
        self.matches = set()

    @property
    def comp(self):
        return self.front + self.word + self.back

    def copy_class(self):
        word_copy = Word.__new__(Word)
        word_copy.__dict__.update(self.__dict__)
        word_copy.count = Word.count_value
        return word_copy


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def comp(d):
    return f"{d.front}{d.word}{d.back}"


def main():
    tic()

    print("[bright_yellow]sandhi splitter")

    profiler_on = False

    if profiler_on is True:
        profiler = cProfile.Profile()
        profiler.enable()

    # make globally accessable vaiables
    setup()

    time_dict = {}
    global unmatched_len_init
    unmatched_len_init = len(unmatched_set)

    print(f"[green]splitting sandhi [white]{unmatched_len_init:,}")

    for counter, word in enumerate(unmatched_set.copy()):
        bip()
        global w
        w = Word(word)
        matches_dict[word] = []

        # d is a diciotnary of data accessed using dot notation
        d: dict = {
            "count": counter,
            "comm": "start",
            "init": word,
            "front": "",
            "word": word,
            "back": "",
            "rules_front": "",
            "rules_back": "",
            "tried": set(),
            "matches": set(),
            "path": "start",
            "processes": 0
        }
        d = dotdict(d)

        # debug
        # if d.init != "tapantamādiccamivantalikkheti":
        #     continue
        # if d.count > 1000:
        #     break

        if d.count % 1000 == 0:
            print(
                f"{d.count:>10,} / {unmatched_len_init:<10,}{d.word}")

        # two word sandhi
        d = two_word_sandhi(d)

        if matches_dict[word] != []:
            w.matches.add(comp(d))
            d.matches.add(comp(d))
            unmatched_set.discard(word)
            time_dict[word] = bop()

        else:
            # three word sandhi
            d = three_word_sandhi(d)

            if matches_dict[word] != []:
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(word)
                time_dict[word] = bop()

        # recursive removal
        if w.matches == set():
            recursive_removal(d)
            time_dict[word] = bop()

    summary()

    # save matches
    with open(pth["matches_path"], "w") as f:
        for word, data in matches_dict.items():
            for item in data:
                f.write(f"{word}\t")
                for column in item:
                    f.write(f"{column}\t")
                f.write("\n")

    # save timer_dict
    df = pd.DataFrame.from_dict(time_dict, orient="index")
    df = df.sort_values(by=0, ascending=False)
    df.to_csv("sandhi/output/timer.csv", sep="\t")

    if profiler_on:
        profiler.disable()
        profiler.dump_stats('profiler.prof')
        yes_no = input("open profiler? (y/n) ")
        if yes_no == "y":
            popen("tuna profiler.prof")

    toc()


def setup():
    print("[green]importing assets")
    global pth
    pth = get_resource_paths()

    global rules
    rules = import_sandhi_rules()

    global shortlist_set
    shortlist_set = make_shortlist_set()

    global unmatched_set
    with open(pth["unmatched_set_path"], "rb") as f:
        unmatched_set = pickle.load(f)

    global all_inflections_set
    with open(pth["all_inflections_set_path"], "rb") as f:
        all_inflections_set = pickle.load(f)

    global all_inflections_nofirst
    global all_inflections_nolast
    global all_inflections_first3
    global all_inflections_last3

    all_inflections_nofirst,\
        all_inflections_nolast,\
        all_inflections_first3,\
        all_inflections_last3\
        = make_all_inflections_nfl_nll(
            all_inflections_set)

    global matches_dict
    with open(pth["matches_dict_path"], "rb") as f:
        matches_dict = pickle.load(f)


def import_sandhi_rules():
    print("[green]importing sandhi rules", end=" ")

    sandhi_rules_df = pd.read_csv(
        pth["sandhi_rules_path"], sep="\t", dtype=str)
    sandhi_rules_df.fillna("", inplace=True)
    print(f"[white]{len(sandhi_rules_df):,}")
    sandhi_rules = sandhi_rules_df.to_dict('index')

    print("[green]testing sandhi rules for dupes", end=" ")
    dupes = sandhi_rules_df[sandhi_rules_df.duplicated(
        ["chA", "chB", "ch1", "ch2"], keep=False)]

    if len(dupes) != 0:
        print("\n[red]! duplicates found! please remove them and try again")
        print(f"\n[red]{dupes}")
        input("\n[white] press enter to continue")
        import_sandhi_rules()
    else:
        print("[white]ok")

    print("[green]testing sandhi rules for spaces", end=" ")

    if (
        sandhi_rules_df["chA"].str.contains(" ").any() or
        sandhi_rules_df["chB"].str.contains(" ").any() or
        sandhi_rules_df["ch1"].str.contains(" ").any() or
        sandhi_rules_df["ch2"].str.contains(" ").any()
    ):
        print("\n[red]! spaces found! please remove them and try again")
        input("[white]press enter to continue ")
        import_sandhi_rules()

    else:
        print("[white]ok")

    return sandhi_rules


def make_shortlist_set():

    print("[green]making shortlist set", end=" ")

    shortlist_df = pd.read_csv(
        pth["shortlist_path"], dtype=str, header=None, sep="\t")
    shortlist_df.fillna("", inplace=True)

    shortlist_set = set(shortlist_df[0].tolist())
    print(f"[white]{len(shortlist_set)}")

    return shortlist_set


def make_all_inflections_nfl_nll(all_inflections_set):
    """all inflections with no first letter, no last, no first three, no last three"""

    print("[green]making all inflections nfl & nll", end=" ")

    all_inflections_nofirst = set()
    all_inflections_nolast = set()
    all_inflections_first3 = set()
    all_inflections_last3 = set()

    for inflection in all_inflections_set:
        # no first letter
        all_inflections_nofirst.add(inflection[1:])
        # no last letter
        all_inflections_nolast.add(inflection[:-1])
        # leave first 3 letters
        all_inflections_first3.add(inflection[:3])
        # leave last 3 letters
        all_inflections_last3.add(inflection[-3:])

    print(f"[white]{len(all_inflections_nofirst):,}")

    return all_inflections_nofirst, all_inflections_nolast, all_inflections_first3, all_inflections_last3


def remove_neg(d):
    "finds neg in front and 1. finds match 2. recurses 3. passes through"
    d_orig = dotdict(d)

    if comp(d) not in w.matches and len(d.word) > 2:
        d.path += " > neg"

        if d.word.startswith("a"):
            if d.word[1] == d.word[2]:
                d.front = f"na + {d.front}"
                d.word = d.word[2:]
                d.rules_front = "na,"
            else:
                d.front = f"na + {d.front}"
                d.word = d.word[1:]
                d.rules_front = "na,"

        elif d.word.startswith("an"):
            d.front = f"na + {d.front}"
            d.word = d.word[2:]
            d.rules_front = "na,"

        elif d.word.startswith("na"):
            if d.word[1] == d.word[2]:
                d.front = f"na + {d.front}"
                d.word = d.word[3:]
                d.rules_front = "na,"
            else:
                d.front = f"na + {d.front}"
                d.word = d.word[2:]
                d.rules_front = "na,"

        elif d.word.startswith("nā"):
            d.front = f"na + {d.front}"
            d.word = f"a{d.word[2:]}"
            d.rules_front = "na,"

        if d.word in all_inflections_set:
            d.comm == f"match! = {comp(d)}"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [(
                    comp(d), "xword-na", "na", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing from na"
            recursive_removal(d)

        d = dotdict(d_orig)

    return d_orig


def remove_sa(d):
    """find sa in front and 1. match 2. recurse 3. pass through"""
    d_orig = dotdict(d)

    if comp(d) not in w.matches and len(d.word) >= 4:
        d.path += " > sa"

        if d.word[2] == d.word[3]:
            d.front = f"sa + {d.front}"
            d.word = d.word[3:]
            d.rules_front = "sa,"

        else:
            d.front = f"sa + {d.front}"
            d.word = d.word[2:]
            d.rules_front = "sa,"

        if d.word in all_inflections_set:
            d.comm = "sa"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-sa", "sa", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing sa"
            recursive_removal(d)

        d = dotdict(d_orig)

    return d_orig


def remove_su(d):
    """find su in front and 1. match 2. recurse 3. pass through"""
    d_orig = dotdict(d)

    if comp(d) not in w.matches and len(d.word) >= 4:
        d.path += " > su"

        if d.word[2] == d.word[3]:
            d.front = f"su + {d.front}"
            d.word = d.word[3:]
            d.rules_front = "su,"

        else:
            d.front = f"su + {d.front}"
            d.word = d.word[2:]
            d.rules_front += "su,"

        if d.word in all_inflections_set:
            d.comm = "su"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-su", "su", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing su"
            recursive_removal(d)

        d = dotdict(d_orig)

    return d_orig


def remove_dur(d):
    """find du(r) in front and 1. match 2. recurse 3. pass through"""
    d_orig = dotdict(d)

    if comp(d) not in w.matches and len(d.word) >= 4:
        d.path += " > dur"

        if d.word[2] == d.word[3]:
            d.front = f"dur + {d.front}"
            d.word = d.word[3:]
            d.rules_front = "dur,"

        else:
            d.front = f"dur + {d.front}"
            d.word = d.word[2:]
            d.rules_front = "dur,"

        if d.word in all_inflections_set:
            d.comm = "dur"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-dur", "dur", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing dur"
            recursive_removal(d)

        d = dotdict(d_orig)

    return d_orig


def remove_apievaiti(d):
    """find api eva or iti using sandhi rules then
    1. match 2. recurse 3. pass through"""

    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        try:
            if d.word[-3] in vowels:
                wordA = d.word[:-3]
                wordB = d.word[-3:]

            else:
                wordA = d.word[:-2]
                wordB = d.word[-2:]

        except Exception:
            wordA = d.word[:-2]
            wordB = d.word[-2:]

        for rule in rules:
            chA = rules[rule]["chA"]
            chB = rules[rule]["chB"]
            ch1 = rules[rule]["ch1"]
            ch2 = rules[rule]["ch2"]

            try:
                wordA_lastletter = wordA[-1]
            except Exception:
                wordA_lastletter = wordA
            wordB_firstletter = wordB[0]

            if (wordA_lastletter == chA and
                    wordB_firstletter == chB):
                word1 = wordA[:-1] + ch1
                word2 = ch2 + wordB[1:]

                if word2 in ["api", "eva", "iti"]:
                    d.word = d.word.replace(wordB, "")
                    d.word = d.word.replace(wordA, word1)
                    d.back = f" + {word2}{d.back}"
                    d.comm = "apievaiti"
                    d.rules_back = f"{rule+2},{d.rules_back}"
                    d.path += " > apievaiti"

                    if d.word in all_inflections_set:
                        d.comm == f"match! = {comp(d)}"

                        if comp(d) not in w.matches:
                            matches_dict[d.init] += [
                                (comp(d), "xword-pi", "apievaiti", d.path)]
                            w.matches.add(comp(d))
                            d.matches.add(comp(d))
                            unmatched_set.discard(d.init)

                    else:
                        recursive_removal(d)

                    d = dotdict(d_orig)

    return d_orig


def remove_lwff_clean(d):
    """find a list of longest clean words from the front then 
    1. match 2. redcurse or pass through"""

    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        lwff_clean_list = []

        for i in range(len(d.word)):
            if d.word[:-i] in all_inflections_set:
                lwff_clean_list.append(d.word[:-i])

        # if lwff_clean_list:
        #     print(len(min(lwff_clean_list, key=len)))

        for lwff_clean in lwff_clean_list:

            if len(lwff_clean) > 1:
                d.path += " > lwff_clean"
                d.word = re.sub(f"^{lwff_clean}", "", d.word, count=1)
                d.front = f"{d.front}{lwff_clean} + "
                d.comm = f"lwff_clean [yellow]{lwff_clean}"
                d.rules_front += "0,"

                if d.word in all_inflections_set:

                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [
                            (comp(d), "xword-lwff", f"{comp_rules(d)}", d.path)]
                        w.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                else:
                    d.comm = f"recursing lwff_clean [yellow]{comp(d)}"
                    recursive_removal(d)

                d = dotdict(d_orig)

    return d_orig


def remove_lwfb_clean(d):
    """find list of longest words from the back then
    1. match 2. recurse 3. pass through"""

    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        lwfb_clean_list = []

        for i in range(len(d.word)):
            if d.word[i:] in all_inflections_set:
                lwfb_clean_list.append(d.word[i:])

        # if lwfb_clean_list:
        #     print(len(min(lwfb_clean_list, key=len)))

        for lwfb_clean in lwfb_clean_list:

            if len(lwfb_clean) > 1:
                d.path += " > lwfb_clean"
                d.word = re.sub(f"{lwfb_clean}$", "", d.word, count=1)
                d.back = f" + {lwfb_clean}{d.back}"
                d.comm = f"lwfb_clean [yellow]{lwfb_clean}"
                d.rules_back = f"0,{d.rules_back}"

                if d.word in all_inflections_set:
                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [
                            (comp(d), "xword-lwfb", f"{comp_rules(d)}", d.path)]
                        w.matches.add(comp(d))
                        d.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                else:
                    d.comm = f"recursing lfwb_clean [yellow]{comp(d)}"
                    recursive_removal(d)

                d = dotdict(d_orig)

    return d_orig


def remove_lwff_fuzzy(d):
    """find list of longest fuzzy words from the front then
    1. match 2. recurse 3. pass through"""

    d_orig = dotdict(d)

    if comp(d) not in d.matches:

        lwff_fuzzy_list = []

        if len(d.word) >= 1:
            for i in range(len(d.word)):
                fuzzy_word = d.word[:-i]

                if fuzzy_word in all_inflections_nolast:
                    lwff_fuzzy_list.append(fuzzy_word)

        # if lwff_fuzzy_list:
        #     print(len(min(lwff_fuzzy_list, key=len)))

        for lwff_fuzzy in lwff_fuzzy_list:

            if len(lwff_fuzzy) >= 1:

                try:
                    if (lwff_fuzzy[-1]) in vowels:
                        wordA_fuzzy = lwff_fuzzy[:-1]
                    else:
                        wordA_fuzzy = lwff_fuzzy
                except Exception:
                    wordA_fuzzy = lwff_fuzzy
                wordB_fuzzy = re.sub(f"^{wordA_fuzzy}", "", d.word, count=1)

                try:
                    wordA_lastletter = wordA_fuzzy[-1]
                except Exception:
                    wordA_lastletter = ""
                try:
                    wordB_firstletter = wordB_fuzzy[0]
                except Exception:
                    wordB_firstletter = ""

                for rule in rules:
                    chA = rules[rule]["chA"]
                    chB = rules[rule]["chB"]
                    ch1 = rules[rule]["ch1"]
                    ch2 = rules[rule]["ch2"]

                    if (wordA_lastletter == chA and
                            wordB_firstletter == chB):
                        word1 = wordA_fuzzy[:-1] + ch1
                        word2 = ch2 + wordB_fuzzy[1:]

                        if word1 in all_inflections_set:
                            d.path += " > lwff_fuzzy"
                            d.word = re.sub(f"^{wordA_fuzzy}", "", d.word, count=1)
                            d.word = re.sub(f"^{wordB_fuzzy}", word2, d.word, count=1)
                            d.front = f"{d.front}{word1} + "
                            d.comm = f"lwff_fuzzy [yellow]{word1} + {word2}"
                            d.rules_front += f"{rule+2},"

                            if d.word in all_inflections_set:
                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [
                                        (comp(d), "xword-fff", f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                            else:
                                d.comm = f"recursing lwff_fuzzy [yellow]{comp(d)}"
                                d.path += "> lwff_fuzzy"
                                recursive_removal(d)

                            d = dotdict(d_orig)

    return d_orig


def remove_lwfb_fuzzy(d):
    """find fuzzy list of longest words fuzzy from the back then
    1. match 2. recurse 3. pass through"""

    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        lwfb_fuzzy_list = []

        if len(d.word) >= 1:
            for i in range(len(d.word)):
                fuzzy_word = d.word[i:]

                if fuzzy_word in all_inflections_nofirst:
                    lwfb_fuzzy_list.append(fuzzy_word)

        # if lwfb_fuzzy_list:
        #     print(len(min(lwfb_fuzzy_list, key=len)))

        for lwfb_fuzzy in lwfb_fuzzy_list:

            if len(lwfb_fuzzy) >= 1:
                wordA_fuzzy = re.sub(f"{lwfb_fuzzy}$", "", d.word, count=1)
                wordB_fuzzy = lwfb_fuzzy

                # !!! the problem is fuzzy words starting with a consonsant
                # and the previous word ending with a vowel wont be recognised by rules
                # which all start with a consonant followed by a vowel

                try:
                    if wordB_fuzzy[0] not in vowels:
                        wordB_fuzzy = wordA_fuzzy[-1] + wordB_fuzzy
                        wordA_fuzzy = wordA_fuzzy[:-1]
                except Exception:
                    pass

                try:
                    wordA_lastletter = wordA_fuzzy[-1]
                except Exception:
                    wordA_lastletter = ""
                try:
                    wordB_firstletter = wordB_fuzzy[0]
                except Exception:
                    wordB_firstletter = ""

                for rule in rules:
                    chA = rules[rule]["chA"]
                    chB = rules[rule]["chB"]
                    ch1 = rules[rule]["ch1"]
                    ch2 = rules[rule]["ch2"]

                    if (wordA_lastletter == chA and
                            wordB_firstletter == chB):
                        word1 = wordA_fuzzy[:-1] + ch1
                        word2 = ch2 + wordB_fuzzy[1:]

                        if word2 in all_inflections_set:
                            d.path += " > lwfb_fuzzy"
                            d.word = re.sub(
                                f"{wordB_fuzzy}$", "", d.word, count=1)
                            d.word = re.sub(
                                f"{wordA_fuzzy}$", word1, d.word, count=1)
                            # d.back = re.sub(
                            #     f"{wordB_fuzzy}$", word2, d.back, count=1)
                            d.back = f" + {word2}{d.back}"
                            d.comm = f"lwfb_fuzzy [yellow]{word1} + {word2}"
                            d.rules_back = f"{rule+2},{d.rules_back}"

                            if d.word in all_inflections_set:
                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [
                                        (comp(d), "xword-fbf", f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                            else:
                                d.comm = f"recursing lwfb_fuzzy [yellow]{comp(d)}"
                                recursive_removal(d)

                            d = dotdict(d_orig)

    return d_orig


def two_word_sandhi(d):
    """split into two words and then
    1. match or 2. pass through
    """

    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        for x in range(0, len(d.word)-1):

            wordA = d.word[:-x-1]
            wordB = d.word[-1-x:]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""
            wordB_firstletter = wordB[0]

            # blah blah

            if (wordA in all_inflections_set and
                    wordB in all_inflections_set):
                d.front = f"{d.front}{wordA} + "
                d.word = wordB
                d.rules_front += "0,"
                d.path += " > 2.1"
                if d.comm == "start":
                    d.comm = "start2.1"
                else:
                    d.comm = "x2.1"

                if comp(d) not in d.matches:
                    matches_dict[d.init] += [
                        (f"{d.front}{wordB}{d.back}", d.comm, comp_rules(d), d.path)]
                    w.matches.add(comp(d))
                    d.matches.add(comp(d))
                    unmatched_set.discard(d.init)

                d = dotdict(d_orig)

            # bla* *lah

            for rule in rules:
                chA = rules[rule]["chA"]
                chB = rules[rule]["chB"]
                ch1 = rules[rule]["ch1"]
                ch2 = rules[rule]["ch2"]

                if (wordA_lastletter == chA and
                        wordB_firstletter == chB):
                    word1 = wordA[:-1] + ch1
                    word2 = ch2 + wordB[1:]

                    if (word1 in all_inflections_set and
                            word2 in all_inflections_set):
                        d.front = f"{d.front}{word1} + "
                        d.word = word2
                        d.rules_front += f"{rule+2},"
                        d.path += " > 2.2"
                        if d.comm == "start":
                            d.comm = "start2.2"
                        else:
                            d.comm = "x2.2"

                        if comp(d) not in w.matches:
                            matches_dict[d.init] += [
                                (comp(d), d.comm, f"{comp_rules(d)}", d.path)]
                            w.matches.add(comp(d))
                            d.matches.add(comp(d))
                            unmatched_set.discard(d.init)

                    d = dotdict(d_orig)

    return d_orig


def three_word_sandhi(d):
    """split into three words then
    1. match or 2. pass through"""
    d_orig = dotdict(d)

    if comp(d) not in w.matches:

        for x in range(0, len(d.word)-1):

            wordA = d.word[:-x-1]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""

            for y in range(0, len(d.word[-1-x:])-1):
                wordB = d.word[-1-x:-y-1]
                try:
                    wordB_firstletter = wordB[0]
                except Exception:
                    wordB_firstletter = ""
                try:
                    wordB_lastletter = wordB[len(wordB)-1]
                except Exception:
                    wordB_lastletter = ""

                wordC = d.word[-1-y:]
                wordC_firstletter = wordC[0]

                # blah blah blah

                if (wordA in all_inflections_set and
                    wordB in all_inflections_set and
                        wordC in all_inflections_set):

                    d.front = f"{d.front}{wordA} + "
                    d.word = wordB
                    d.back = f" + {wordC}{d.back}"
                    d.rules_front += "0,"
                    d.rules_back = f"0,{d.rules_back}"
                    d.path += " > 3.1"
                    if d.comm == "start":
                        d.comm = "start3.1"
                    else:
                        d.comm = "x3.1"

                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [
                            (comp(d), d.comm, "0,0", d.path)]
                        w.matches.add(comp(d))
                        d.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                    d = dotdict(d_orig)

                # blah bla* *lah
                if wordA in all_inflections_set:

                    for rule in rules:
                        chA = rules[rule]["chA"]
                        chB = rules[rule]["chB"]
                        ch1 = rules[rule]["ch1"]
                        ch2 = rules[rule]["ch2"]

                        if (wordB_lastletter == chA and
                                wordC_firstletter == chB):
                            word2 = wordB[:-1] + ch1
                            word3 = ch2 + wordC[1:]

                            if (wordA in all_inflections_set and
                                word2 in all_inflections_set and
                                    word3 in all_inflections_set):

                                d.front = f"{d.front}{wordA} + "
                                d.word = word2
                                d.back = f" + {word3}{d.back}"
                                d.rules_front += f"0,"
                                d.rules_back = f"{rule+2},{d.rules_back}"
                                d.path += " > 3.2"
                                if d.comm == "start":
                                    d.comm = "start3.2"
                                else:
                                    d.comm = "x3.2"

                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [
                                        (comp(d), d.comm, f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                                d = dotdict(d_orig)

                # bla* *lah blah

                if wordC in all_inflections_set:

                    for rule in rules:
                        chA = rules[rule]["chA"]
                        chB = rules[rule]["chB"]
                        ch1 = rules[rule]["ch1"]
                        ch2 = rules[rule]["ch2"]

                        if (wordA_lastletter == chA and
                                wordB_firstletter == chB):
                            word1 = wordA[:-1] + ch1
                            word2 = ch2 + wordB[1:]

                            if (word1 in all_inflections_set and
                                word2 in all_inflections_set and
                                    wordC in all_inflections_set):

                                d.front = f"{d.front}{word1} + "
                                d.word = word2
                                d.back = f" + {wordC}{d.back}"
                                d.rules_front += f"{rule+2},"
                                d.rules_back = f"0,{d.rules_back}"
                                d.path += " > 3.3"
                                if d.comm == "start":
                                    d.comm = "start3.3"
                                else:
                                    d.comm = "x3.3"

                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [
                                        (comp(d), d.comm, f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                                d = dotdict(d_orig)

                # bla* *la* *lah

                for rulex in rules:
                    chAx = rules[rulex]["chA"]
                    chBx = rules[rulex]["chB"]
                    ch1x = rules[rulex]["ch1"]
                    ch2x = rules[rulex]["ch2"]

                    if (wordA_lastletter == chAx and
                            wordB_firstletter == chBx):
                        word1 = wordA[:-1] + ch1x
                        word2 = ch2x + wordB[1:]

                        for ruley in rules:
                            chAy = rules[ruley]["chA"]
                            chBy = rules[ruley]["chB"]
                            ch1y = rules[ruley]["ch1"]
                            ch2y = rules[ruley]["ch2"]

                            if (wordB_lastletter == chAy and
                                    wordC_firstletter == chBy):
                                word2 = (ch2x + wordB[1:])[:-1] + ch1y
                                word3 = ch2y + wordC[1:]

                                if (word1 in all_inflections_set and
                                        word2 in all_inflections_set and
                                        word3 in all_inflections_set):

                                    d.front = f"{d.front}{word1} + "
                                    d.word = word2
                                    d.back = f" + {word3}{d.back}"
                                    d.rules_front += f"{rulex+2},"
                                    d.rules_back = f"{ruley+2},{d.rules_back}"
                                    d.path += " > 3.4"
                                    if d.comm == "start":
                                        d.comm = "start3.4"
                                    else:
                                        d.comm = "x3.4"

                                    if comp(d) not in w.matches:
                                        matches_dict[d.init] += [
                                            (comp(d), d.comm, f"{comp_rules(d)}", d.path)]
                                        w.matches.add(comp(d))
                                        d.matches.add(comp(d))
                                        unmatched_set.discard(d.init)

                                    d = dotdict(d_orig)

    return d_orig


def comp_rules(d):
    return f"{d.rules_front}{d.rules_back}"


def dprint(d):
    print(f"count:\t{d.count}")
    print(f"comm:\t{d.comm}")
    print(f"init:\t'{d.init}'")
    print(f"front:\t[blue]'{d.front}'")
    print(f"word:\t[blue]'{d.word}'")
    print(f"back:\t[blue]'{d.back}'")
    print(f"comp:\t[yellow]{comp(d)}")
    print(f"rules_front:\t{d.rules_front}")
    print(f"rules_back:\t{d.rules_back}")
    # print(f"tried:\t{d.tried}")
    print(f"matches:\t{d.matches}")
    print(f"path:\t{d.path}")
    print(f"processes:\t{d.processes}")
    print()


def summary():

    with open("sandhi/output/unmatched.csv", "w") as f:
        for item in unmatched_set:
            f.write(f"{item}\n")

    unmatched = len(unmatched_set)
    umatched_perc = (unmatched/unmatched_len_init)*100
    matched = unmatched_len_init-len(unmatched_set)
    matched_perc = (matched/unmatched_len_init)*100

    print(
        f"[green]unmatched:\t{unmatched:,} / {unmatched_len_init:,}\t[white]{umatched_perc:.2f}%")
    print(
        f"[green]matched:\t{matched:,} / {unmatched_len_init:,}\t[white]{matched_perc:.2f}%")

    word_count = len(matches_dict)
    match_count = 0

    for word, matches in matches_dict.items():
        match_count += len(matches)

    match_average = match_count / word_count

    print(f"[green]match count:\t{match_count:,}")
    print(f"[green]match average:\t{match_average:.4f}")


def recursive_removal(d):

    d.processes += 1

    if d.processes < 15:

        # add to matches

        if comp(d) not in w.tried:
            w.tried.add(comp(d))
            d.tried.add(comp(d))

            if d.word in all_inflections_set:
                if comp(d) not in w.matches:
                    matches_dict[d.init] += [
                        (comp(d), f"xword{d.comm}", f"{comp_rules(d)}", d.path)]
                    w.matches.add(comp(d))
                    d.matches.add(comp(d))
                    unmatched_set.discard(d.init)

            else:
                # recursion

                if d.processes == 1:

                    # negatives
                    if d.word.startswith(("a", "na", "an", "nā")):
                        d = remove_neg(d)

                    # sa
                    elif d.word.startswith("sa"):
                        d = remove_sa(d)

                    # su
                    elif d.word.startswith("su"):
                        d = remove_su(d)

                    # dur
                    elif d.word.startswith("du"):
                        d = remove_dur(d)

                # api eva iti
                if re.findall("(pi|va|ti)$", d.word) != []:
                    d = remove_apievaiti(d)

                # two word sandhi
                if d.comm != "start":
                    d = two_word_sandhi(d)

                    if not d.matches:
                        # three word sandhi
                        d = three_word_sandhi(d)

                    # ffc = lwff clean
                    d = remove_lwff_clean(d)

                    # fbc = lwfb_clean
                    d = remove_lwfb_clean(d)

                    # fff = lwff fuzzy
                    d = remove_lwff_fuzzy(d)

                    # fbf = lwfb fuzzy
                    d = remove_lwfb_fuzzy(d)


if __name__ == "__main__":
    main()


# two word three word sandhi use comment when writing to dict
# in lwff lwffb, don't use the whole lists
# fix rules
# add ttā and its inflections to all inflections
# think of some sanity tests

# csv > tsv

# iṭṭhārammaṇānubhavanārahe iṭṭhārammaṇa + anu + bhavanā
# dakkhiṇadisābhāgo   dakkhiṇadisābhi + āgo

# why are some words taking so long?
# too many clean and fuzzy words getting recursed

# guṇavaṇṇābhāvena
# must show negative

# khayasundarābhirūpaabbhanumodanādīsu

# dibbacakkhuñāṇavipassanāñāṇamaggañāṇaphalañāṇapaccavekkhaṇañāṇānametaṃ
# end etaṃ is getting lost!

# only add words to matches that aren't already there.

# unmatched:      2627 / 51972    5.05%
# matched:        49345 / 51972   94.95%
# ----------------------------------------
# 0:48:24.987711
# = 5.387516355 hours

# include neg count in post process

# kusalākusalasāvajjānavajjasevitabbāsevitabbahīna
# lots of results have lettercoutn less than the word iteself!

