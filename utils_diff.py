from difflib import SequenceMatcher
import re, nltk

stopwords = nltk.corpus.stopwords.words('english')
stopwords += [".", ",", "?", "!", ";", ":", "\n", "-"]
stopwords = set(stopwords)


def tokenize(text):
    text = re.sub(r"\s{2,}", " ", text)
    text = text.replace("—", "-").replace("–", "-")
    cleaned_text = text.replace(".", " .").replace(",", " ,").replace("!", " !").replace("?", " ?").replace(";", " ;").replace(":", " :").replace("\n", " \n ").replace("'", " '").replace('"', ' " ').replace("(", " (").replace(")", " )")
    cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text)
    return cleaned_text.split(" ")


def fix_punctuation(text):
    return text.replace(" .", ".").replace(" ,", ",").replace(" !", "!").replace(" ?", "?").replace(" ;", ";").replace(" :", ":").replace(" \n", "\n ").replace(" '", "'").replace(' "', '"').replace(" (", "(").replace(" )", ")")


def untokenize(tokens):
    return fix_punctuation(" ".join(tokens))


def remove_stop_words(tokens):
    # Expecting tokenized text
    assert type(tokens) == list
    return [t for t in tokens if t.lower() not in stopwords]


def split_sent_text(text):
    if "." not in text:
        return [text]

    toks = [txt for txt in text.split(".")]
    N = len(toks)
    toks = [t+"." if i < N-1 else t for i, t in enumerate(toks)]

    merged_toks = []
    build_up = ""
    for tok in toks:
        # Merge if it is single letters (like U.S. )
        if len(tok) == 2 and tok[:-1].isalpha():
            build_up += tok
        else:
            if len(build_up) > 0:
                merged_toks.append(build_up)
            merged_toks.append(tok)
            build_up = ""

    if len(merged_toks) > 0 and len(merged_toks[-1].strip()) == 0:
        merged_toks = merged_toks[:-1]
    return merged_toks


def split_edits_on_sentence(operations):
    new_operations = []
    for old_op in operations:
        if old_op["type"] == "equal":
            new_operations.append({"type": "equal", "text": old_op["text"], "N_words": old_op["N_words"]})
        if "delete" in old_op:
            del_toks = split_sent_text(old_op["delete"])
            for del_tok in del_toks:
                new_operations.append({"type": "delete", "delete": del_tok, "N_words": del_tok.count(" ")+1})
        if "insert" in old_op:
            ins_toks = split_sent_text(old_op["insert"])
            for ins_tok in ins_toks:
                new_operations.append({"type": "insert", "insert": ins_tok, "N_words": ins_tok.count(" ")+1})        
    return new_operations


def get_edit_operations(text1, text2, split_replace=False, split_sentences=False, remove_stop_ws=False):
    S1 = tokenize(text1)
    S2 = tokenize(text2)
    if remove_stop_ws:
        S1 = remove_stop_words(S1)
        S2 = remove_stop_words(S2)

    s = SequenceMatcher(None, S1, S2)
    opcodes = s.get_opcodes()
    operations = []
    for code, i1, i2, j1, j2 in opcodes:
        if code == "insert":
            operations.append({"type": "insert", "insert": untokenize(S2[j1:j2]), "N_words": len(S2[j1:j2])})
        if code == "delete":
            operations.append({"type": "delete", "delete": untokenize(S1[i1:i2]), "N_words": len(S1[i1:i2])})
        if code == "replace":
            if split_replace:
                operations.append({"type": "insert", "insert": untokenize(S2[j1:j2]), "N_words": len(S1[i1:i2])})
                operations.append({"type": "delete", "delete": untokenize(S1[i1:i2]), "N_words": len(S2[j1:j2])})
            else:
                operations.append({"type": "replace", "insert": untokenize(S2[j1:j2]), "delete": untokenize(S1[i1:i2]), "N_words": len(S2[j1:j2])+len(S1[i1:i2])})
        if code == "equal":
            operations.append({"type": "equal", "text": untokenize(S1[i1:i2]), "N_words": len(S1[i1:i2])})
    if split_sentences:
        operations = split_edits_on_sentence(operations)
    return operations


def make_color(text, color, style="shell"):
    assert color in ["green", "red", "blue"]
    assert style in ["shell", "xml", "html", "llm", "latex"]

    if style == "shell":
        start_green, end_green = "\033[1;32m", "\033[0m"
        start_red, end_red = "\033[1;31m", "\033[0m"
        start_blue, end_blue = "\033[1;34m", "\033[0m"
    elif style == "xml":
        start_green, end_green = " <ins> ", " </ins> "
        start_red, end_red = " <del> ", " </del> "
        start_blue, end_blue = " <blue> ", " </blue> "
    elif style == "latex":
        start_green, end_green = " \hlblue{", "} "
        start_red, end_red = " \hlred{", "} "
        start_blue, end_blue = " \hlblue{ ", " } "
    elif style == "html":
        start_green, end_green = " <span class='green'> ", " </span> "
        start_red, end_red = " <span class='red'> ", " </span> "
        start_blue, end_blue = " <span class='blue'> ", " </span> "
    elif style == "llm":
        start_green, end_green = " ADD ", " EADD "
        start_red, end_red = " DEL ", " EDEL "
        start_blue, end_blue = " INFO ", " EINFO "

    if color == "green":
        return start_green + text + end_green
    elif color == "red":
        return start_red + text + end_red
    elif color == "blue":
        return start_blue + text + end_blue


def make_colored_text(text1, text2, style="shell", split_replace=False, split_sentences=False, remove_stop_ws=False):
    operations = get_edit_operations(text1, text2, split_replace=split_replace, split_sentences=split_sentences, remove_stop_ws=remove_stop_ws)
    return make_colored_text_from_operations(operations, style=style)


def make_colored_text_from_operations(operations, style="shell"):
    colored_text = ""
    for operation in operations:
        if operation["type"] == "insert":
            colored_text += make_color(operation["insert"], "green", style=style)
        if operation["type"] == "delete":
            colored_text += make_color(operation["delete"], "red", style=style)
        if operation["type"] == "replace":
            colored_text += make_color(operation["delete"], "red", style=style) + make_color(operation["insert"], "green", style=style)
        if operation["type"] == "equal":
            colored_text += " " + operation["text"]

    lines = [line.strip() for line in colored_text.split("\n")]
    text = fix_punctuation("\n".join(lines))
    # Replace 2+ spaces by 1 space with re
    text = re.sub(r"\s{2,}", " ", text)
    return text


def highlight_operations(operations, op_idxs, style="shell"):
    # Should be refactored, there's overlap
    colored_text = ""

    if style == "shell":
        start_green, end_green = "\033[1;32m", "\033[0m"
        start_red, end_red = "\033[1;31m", "\033[0m"
    elif style == "xml":
        start_green, end_green = " <green> ", " </green> "
        start_red, end_red = " <red> ", " </red> "
    else:
        start_green, end_green = " ADD ", " END "
        start_red, end_red = " DEL ", " END "

    for idx, operation in enumerate(operations):
        if operation["type"] == "equal":
            colored_text += " " + operation["text"]
        elif idx in op_idxs:
            if operation["type"] == "insert":
                colored_text += start_green + operation["insert"] + end_green
            if operation["type"] == "delete":
                colored_text += start_red + operation["delete"] + end_red
            if operation["type"] == "replace":
                colored_text += start_red + operation["delete"] + end_red + " " + start_green + operation["insert"] + end_green
        else:
            if operation["type"] == "insert":
                pass
            if operation["type"] == "delete":
                colored_text += " " + operation["delete"] + " "
            if operation["type"] == "replace":
                colored_text += " " + operation["delete"] + " "

    lines = [line.strip() for line in colored_text.split("\n")]
    text = fix_punctuation("\n".join(lines))
    # Replace 2+ spaces by 1 space with re
    text = re.sub(r"\s{2,}", " ", text)
    return text

def remove_operations(operations, op_idxs, style="shell"):
    # Should be refactored, there's overlap
    colored_text = ""

    if style == "shell":
        start_green, end_green = "\033[1;32m", "\033[0m"
        start_red, end_red = "\033[1;31m", "\033[0m"
    elif style == "xml":
        start_green, end_green = " <ins> ", " </ins> "
        start_red, end_red = " <del> ", " </del> "
    elif style == "none":
        start_green, end_green = " ", " "
        start_red, end_red = " ", " "
    else:
        start_green, end_green = " ADD ", " END "
        start_red, end_red = " DEL ", " END "

    for idx, operation in enumerate(operations):
        if operation["type"] == "equal":
            colored_text += " " + operation["text"]
        elif idx not in op_idxs:
            if operation["type"] == "insert":
                colored_text += start_green + operation["insert"] + end_green
            if operation["type"] == "delete":
                if style != "none":
                    colored_text += start_red + operation["delete"] + end_red
            if operation["type"] == "replace":
                if style != "none":
                    start_red + operation["delete"] + end_red + " "
                colored_text += start_green + operation["insert"] + end_green
        else:
            if operation["type"] == "insert":
                pass
            if operation["type"] == "delete":
                colored_text += " " + operation["delete"] + " "
            if operation["type"] == "replace":
                colored_text += " " + operation["delete"] + " "

    lines = [line.strip() for line in colored_text.split("\n")]
    text = fix_punctuation("\n".join(lines))
    # Replace 2+ spaces by 1 space with re
    text = re.sub(r"\s{2,}", " ", text)
    return text


def compute_equal_ratio(text1, text2, partial=False, remove_stop_ws=False):
    operations = get_edit_operations(text1, text2, remove_stop_ws=remove_stop_ws)
    equal_idx = [i for i, operation in enumerate(operations) if operation["type"] == "equal"]

    # We're letting go of start and end edits
    if partial and len(equal_idx) > 0:        
        operations = operations[equal_idx[0]:equal_idx[-1]+1]

    N_equal, N_total = 0, 0
    for operation in operations:
        N_total += operation["N_words"]
        if operation["type"] == "equal":
            N_equal += operation["N_words"]
    return N_equal / N_total


def compute_addition_ratio(text1, text2):
    operations = get_edit_operations(text1, text2)

    N_added, N_removed = 0, 0
    for op in operations:
        if op["type"] == "insert":
            N_added += op["N_words"]
        if op["type"] == "delete":
            N_removed += op["N_words"]

    return (N_removed - N_added) / (max(N_added, N_removed)+1)


def construct_partial_pair(text1, text2):
    operations = get_edit_operations(text1, text2)
    equal_idx = [i for i, operation in enumerate(operations) if operation["type"] == "equal"]
    if len(equal_idx) > 0:
        # We're letting go of start and end edits
        operations = operations[equal_idx[0]:equal_idx[-1]+1]

    partial_text1 = ""
    partial_text2 = ""
    for operation in operations:
        if operation["type"] == "insert":
            partial_text2 += " " + operation["insert"]
        if operation["type"] == "delete":
            partial_text1 += " " + operation["delete"]
        if operation["type"] == "replace":
            partial_text1 += " " + operation["delete"]
            partial_text2 += " " + operation["insert"]
        if operation["type"] == "equal":
            partial_text1 += " " + operation["text"]
            partial_text2 += " " + operation["text"]
    partial_text1 = fix_punctuation(partial_text1)
    partial_text2 = fix_punctuation(partial_text2)
    return partial_text1, partial_text2


# Next up is the overlap samples (for IAA)
def is_completed(d, anno_name):
    anno_key = "annotations_%s" % anno_name
    if anno_key not in d:
        return False
    for idx, e in enumerate(d["edits"]):
        e["idx"] = idx

    to_annotate_idxs = set([e["idx"] for e in d["edits"] if e["type"] != "equal"])
    annotated_idxs = set([idx for anno in d[anno_key] for idx in anno["edit_idxs"]])
    return to_annotate_idxs == annotated_idxs


def cleanup_annotation(annotations, edits):
    stop_words = ["of", "in", "the", "on", "or", "and", "it", "its", "a", "in the", ";", ","]
    num_fixes = 0
    swaps = []
    annotations = [anno for anno in annotations if len(anno["edit_idxs"]) > 0]
    for anno in annotations:
        inserts = [edits[idx].get("insert", "") for idx in anno["edit_idxs"]]
        deletes = [edits[idx].get("delete", "") for idx in anno["edit_idxs"]]
        inserts = [txt for txt in inserts if len(txt) > 0]
        deletes = [txt for txt in deletes if len(txt) > 0]

        # The edits is only stop words
        if all([txt.lower() in stop_words for txt in inserts]) and all([txt.lower() in stop_words for txt in deletes]):
            if anno["edit_type"] != "syntactic_generic":
                swaps.append((anno["edit_type"], "syntactic_generic"))
                anno["edit_type"] = "syntactic_generic"
                num_fixes += 1

    # Make all semantic deletions adjacent
    sem_del_idxs = [idx for anno in annotations for idx in anno["edit_idxs"] if anno["edit_type"] == "semantic_deletion"]
    sem_del_idxs = sorted(sem_del_idxs)
    new_sem_annos = []

    current_idxs = []
    for idx in sem_del_idxs:
        if len(current_idxs) == 0:
            current_idxs.append(idx)
        else:
            if idx == current_idxs[-1] + 1:
                current_idxs.append(idx)
            else:
                new_sem_annos.append({"edit_type": "semantic_deletion", "edit_idxs": current_idxs})
                current_idxs = [idx]
    if len(current_idxs) > 0:
        new_sem_annos.append({"edit_type": "semantic_deletion", "edit_idxs": current_idxs})
    annotations = [anno for anno in annotations if anno["edit_type"] != "semantic_deletion"]
    annotations += new_sem_annos

    # Resort by min edit_idx in anno
    annotations = sorted(annotations, key=lambda x: min(x["edit_idxs"]))
    return annotations, num_fixes, swaps


class DiffScorer:
    def __init__(self, type="equal_ratio"):
        assert type in ["equal_ratio", "equal_ratio_partial", "addition_ratio", "equal_ratio_nostop", "equal_ratio_partial_nostop"]
        self.type = type
        self.nostop = "nostop" in type
        self.partial = "partial" in type

    def score_one(self, text1, text2):
        if self.type == "addition_ratio":
            return compute_addition_ratio(text1, text2)
        else:
            return compute_equal_ratio(text1, text2, partial=self.partial, remove_stop_ws=self.nostop)

    def score(self, texts1, texts2):
        assert len(texts1) == len(texts2)
        scores = []
        for text1, text2 in zip(texts1, texts2):
            scores.append(self.score_one(text1, text2))
        return {"scores": scores}


if __name__ == "__main__":
    # text1 = "Yelko Gómez (born March 9, 1989, Chiriquí Province) is a Panamanian cyclist riding for Wilier Panama."
    # text2 = "Yelko Gómez (born March 9, 1989 in Chiriquí Province) is a Panamanian cyclist. He is riding for Hyundai-Momi-Continental."
    # print(get_edit_operations(text1, text2, split_replace=True, split_sentences=True))

    r_content = 'Frederick Hubbard "Fred" Gwynne (10 July 1926 – 2 July 1993) was an American actor. Gwynne is best known for his roles as Francis Muldoon and Herman Munster in the 1960s sitcoms Car 54, Where Are You? and The Munsters, respectively, and as Jud Crandall in "Pet Semetary."'
    s_content = "Fred Gwynne (July 10,1926-1993) was an American actor. He was best known for his role as Herman Munster on The Munsters. He also wrote a series of children's books."
    # edits = get_edit_operations(r_content, s_content, split_replace=True, split_sentences=True)
    print(make_colored_text(r_content, s_content, split_replace=True, split_sentences=True))
    print("---")

    # print("[%.3f] %s "% (compute_equal_ratio(text1, text2, remove_stop_ws=False), make_colored_text(text1, text2, remove_stop_ws=False)))
    # print("------")
    # print("[%.3f] %s "% (compute_equal_ratio(text1, text2, remove_stop_ws=True), make_colored_text(text1, text2, remove_stop_ws=True)))
