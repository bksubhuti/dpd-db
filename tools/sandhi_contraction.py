"""Finds all words in examples and commentary that contain an apostrophe
denoting sandhi or contraction, eg. ajj'uposatho, tañ'ca"""

from typing import Dict, List, Set, TypedDict

from rich import print

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.pali_alphabet import pali_alphabet
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    sandhi_contractions: dict = make_sandhi_contraction_dict(db_session)
    counter = 0

    exceptions = [
        "maññeti",
        "āyataggaṃ",
    ]

    filepath = pth.temp_dir.joinpath("sandhi_contraction.tsv")
    with open(filepath, "w") as f:
        for key, values in sandhi_contractions.items():
            contractions = values["contractions"]

            if len(contractions) > 1 and key not in exceptions:
                f.write(f"{counter}. {key}: \n")

                for contraction in contractions:
                    f.write(f"{contraction}\n")

                ids = values["ids"]
                f.write(f"/^({'|'.join(ids)})$/\n")
                f.write("\n")
                counter += 1

        print(counter)


class SandhiContrItem(TypedDict):
    contractions: Set[str]
    ids: List[str]


SandhiContractions = Dict[str, SandhiContrItem]


def make_sandhi_contraction_dict(db_session: Session) -> SandhiContractions:
    """Return a list of all sandhi words in db that are split with '."""

    db = db_session.query(PaliWord).all()
    sandhi_contraction: SandhiContractions = dict()
    word_dict: Dict[int, Set[str]] = dict()

    def replace_split(string: str) -> List[str]:
        string = string.replace("<b>", "")
        string = string.replace("</b>", "")
        string = string.replace("<i>", "")
        string = string.replace("</i>", "")

        string = string.replace(".", " ")
        string = string.replace(",", " ")
        string = string.replace(";", " ")
        string = string.replace("!", " ")
        string = string.replace("?", " ")
        string = string.replace("/", " ")
        string = string.replace("-", " ")
        string = string.replace("{", " ")
        string = string.replace("}", " ")
        string = string.replace("(", " ")
        string = string.replace(")", " ")
        string = string.replace(":", " ")
        string = string.replace("\n", " ")
        list = string.split(" ")
        return list

    for i in db:
        word_dict[i.id] = set()

        if i.example_1 is not None and "'" in i.example_1:
            word_list = replace_split(i.example_1)
            for word in word_list:
                if "'" in word:
                    word_dict[i.id].update([word])

        if i.example_2 is not None and "'" in i.example_2:
            word_list = replace_split(i.example_2)
            for word in word_list:
                if "'" in word:
                    word_dict[i.id].update([word])

        if i.commentary is not None and "'" in i.commentary:
            word_list = replace_split(i.commentary)
            for word in word_list:
                if "'" in word:
                    word_dict[i.id].update([word])

    for id, words in word_dict.items():
        for word in words:
            word_clean = word.replace("'", "")

            if word_clean not in sandhi_contraction:
                sandhi_contraction[word_clean] = SandhiContrItem(
                    contractions = {word},
                    ids = [str(id)],
                )

            else:
                if word not in sandhi_contraction[word_clean]["contractions"]:
                    sandhi_contraction[word_clean]["contractions"].add(word)
                    sandhi_contraction[word_clean]["ids"] += [str(id)]
                else:
                    sandhi_contraction[word_clean]["ids"] += [str(id)]

    error_list = []
    for key in sandhi_contraction:
        for char in key:
            if char not in pali_alphabet:
                error_list += char
                print(key)
    if error_list != []:
        print("[red]SANDHI ERRORS IN EG1,2,COMM:", end=" ")
        print([x for x in error_list], end=" ")

    # print(sandhi_contraction)
    return sandhi_contraction


if __name__ == "__main__":
    main()
