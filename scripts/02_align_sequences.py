from __future__ import annotations

import csv
from itertools import groupby

import pandas as pd
from Bio import SeqIO
from Bio.Align import PairwiseAligner

from common import DATA, OUTPUTS, add_generated, add_warning, load_summary, save_summary, validate_nonempty, write_text


FIRST_SITE = 314
SECOND_SITE = 363
FIRST_WINDOW = (300, 330)
SECOND_WINDOW = (350, 375)
FIRST_DELETION_SCAN = (FIRST_SITE - 20, FIRST_SITE + 20)


def read_one_fasta(path):
    validate_nonempty(path, str(path))
    records = list(SeqIO.parse(path, "fasta"))
    if len(records) != 1:
        raise ValueError(f"Expected one FASTA record in {path}, found {len(records)}")
    return records[0]


def reconstruct_alignment(alignment, seq_a: str, seq_b: str) -> tuple[str, str]:
    a_blocks, b_blocks = alignment.aligned
    a_out: list[str] = []
    b_out: list[str] = []
    a_prev = b_prev = 0
    for (a_start, a_end), (b_start, b_end) in zip(a_blocks, b_blocks):
        if a_start > a_prev:
            a_out.append(seq_a[a_prev:a_start])
            b_out.append("-" * (a_start - a_prev))
        if b_start > b_prev:
            a_out.append("-" * (b_start - b_prev))
            b_out.append(seq_b[b_prev:b_start])
        a_out.append(seq_a[a_start:a_end])
        b_out.append(seq_b[b_start:b_end])
        a_prev, b_prev = a_end, b_end
    if a_prev < len(seq_a):
        a_out.append(seq_a[a_prev:])
        b_out.append("-" * (len(seq_a) - a_prev))
    if b_prev < len(seq_b):
        a_out.append("-" * (len(seq_b) - b_prev))
        b_out.append(seq_b[b_prev:])
    return "".join(a_out), "".join(b_out)


def label_for_human_pos(pos: int | None) -> str:
    if pos is None:
        return ""
    labels = []
    if FIRST_WINDOW[0] <= pos <= FIRST_WINDOW[1]:
        labels.append("first_Xa_window_300_330")
    if SECOND_WINDOW[0] <= pos <= SECOND_WINDOW[1]:
        labels.append("second_Xa_window_350_375")
    if pos in (314, 315):
        labels.append("first_Xa_site_equiv_mature_R271_region")
    if pos in (363, 364):
        labels.append("second_Xa_site_equiv_mature_R320_region")
    return ";".join(labels)


def make_rows(h_aln: str, r_aln: str) -> list[dict]:
    rows = []
    h_pos = r_pos = 0
    for idx, (h_aa, r_aa) in enumerate(zip(h_aln, r_aln), start=1):
        if h_aa != "-":
            h_pos += 1
        if r_aa != "-":
            r_pos += 1
        h_num = h_pos if h_aa != "-" else None
        r_num = r_pos if r_aa != "-" else None
        rows.append(
            {
                "alignment_index": idx,
                "human_pos": h_num,
                "human_aa": h_aa,
                "rabbit_pos": r_num,
                "rabbit_aa": r_aa,
                "label": label_for_human_pos(h_num),
            }
        )
    return rows


def format_alignment(h_aln: str, r_aln: str, width: int = 80) -> str:
    chunks = []
    h_pos = r_pos = 0
    for start in range(0, len(h_aln), width):
        h_chunk = h_aln[start : start + width]
        r_chunk = r_aln[start : start + width]
        h_start = h_pos + 1
        r_start = r_pos + 1
        h_pos += sum(aa != "-" for aa in h_chunk)
        r_pos += sum(aa != "-" for aa in r_chunk)
        match = "".join("|" if a == b else " " for a, b in zip(h_chunk, r_chunk))
        chunks.append(f"human {h_start:>4} {h_chunk} {h_pos:>4}")
        chunks.append(f"            {match}")
        chunks.append(f"rabbit {r_start:>4} {r_chunk} {r_pos:>4}")
        chunks.append("")
    return "\n".join(chunks)


def deletion_summary(rows: list[dict]) -> list[dict]:
    gap_rows = [
        row
        for row in rows
        if row["human_pos"] is not None
        and FIRST_DELETION_SCAN[0] <= row["human_pos"] <= FIRST_DELETION_SCAN[1]
        and row["human_aa"] != "-"
        and row["rabbit_aa"] == "-"
    ]
    groups = []
    for _, group in groupby(enumerate(gap_rows), key=lambda item: item[0] - item[1]["human_pos"]):
        block = [item[1] for item in group]
        groups.append(
            {
                "human_start": block[0]["human_pos"],
                "human_end": block[-1]["human_pos"],
                "length": len(block),
                "human_sequence_deleted_in_rabbit": "".join(row["human_aa"] for row in block),
                "alignment_start": block[0]["alignment_index"],
                "alignment_end": block[-1]["alignment_index"],
            }
        )
    return groups


def alignment_excerpt(rows: list[dict], start: int = 294, end: int = 334) -> str:
    selected = [row for row in rows if row["human_pos"] is not None and start <= row["human_pos"] <= end]
    return (
        "human_pos: "
        + " ".join(f"{row['human_pos']:>3}" for row in selected)
        + "\nhuman:    "
        + " ".join(f" {row['human_aa']} " for row in selected)
        + "\nrabbit:   "
        + " ".join(f" {row['rabbit_aa']} " for row in selected)
        + "\n"
    )


def main() -> None:
    summary = load_summary()
    human_path = DATA / "sequences" / "human_P00734.fasta"
    rabbit_path = DATA / "sequences" / "rabbit_F2.fasta"
    if not rabbit_path.exists():
        msg = "Cannot align sequences because data/sequences/rabbit_F2.fasta is missing."
        add_warning(summary, msg)
        write_text(OUTPUTS / "deletion_summary.txt", msg + "\n", summary)
        pd.DataFrame().to_csv(OUTPUTS / "deletion_summary.csv", index=False)
        add_generated(summary, OUTPUTS / "deletion_summary.csv")
        save_summary(summary)
        print(msg)
        return

    human = read_one_fasta(human_path)
    rabbit = read_one_fasta(rabbit_path)
    if len(rabbit.seq) == 0:
        raise ValueError("Rabbit FASTA validation failed: empty sequence")

    human_seq = str(human.seq)
    rabbit_seq = str(rabbit.seq)
    for site, label in [(FIRST_SITE, "first Xa site"), (SECOND_SITE, "second Xa site")]:
        residue = human_seq[site - 1] if len(human_seq) >= site else "?"
        if residue != "R":
            add_warning(
                summary,
                f"Human P00734 precursor position {site} is {residue}, not R; numbering convention may differ for {label}.",
            )

    aligner = PairwiseAligner()
    aligner.mode = "global"
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -10
    aligner.extend_gap_score = -0.5
    alignment = aligner.align(human_seq, rabbit_seq)[0]
    h_aln, r_aln = reconstruct_alignment(alignment, human_seq, rabbit_seq)
    rows = make_rows(h_aln, r_aln)

    aln_txt = DATA / "alignments" / "human_rabbit_global_alignment.txt"
    header = (
        "Human UniProt P00734 precursor sequence is the numbering source of truth.\n"
        "Human precursor 314/315 is labeled as the first Xa site, equivalent to the mature R271 region.\n"
        "Human precursor 363/364 is labeled as the second Xa site, equivalent to the mature R320 region.\n\n"
    )
    write_text(aln_txt, header + format_alignment(h_aln, r_aln), summary)

    aln_csv = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    with aln_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    add_generated(summary, aln_csv)

    deletions = deletion_summary(rows)
    deletion_csv = OUTPUTS / "deletion_summary.csv"
    pd.DataFrame(deletions).to_csv(deletion_csv, index=False)
    add_generated(summary, deletion_csv)
    if deletions:
        summary["deletion_detected"] = True
        text = "Rabbit-alignment gaps near human precursor first Xa site (scan 294-334):\n"
        for deletion in deletions:
            text += (
                f"- human {deletion['human_start']}-{deletion['human_end']} "
                f"({deletion['length']} aa): {deletion['human_sequence_deleted_in_rabbit']}\n"
            )
        text += "\nAlignment excerpt:\n" + alignment_excerpt(rows)
    else:
        summary["deletion_detected"] = False
        text = (
            "No rabbit deletion/gap was detected within +/-20 residues of human precursor Arg314. "
            "This does not match the expected PMID 10030826 finding; verify the rabbit sequence and alignment.\n"
        )
        add_warning(summary, "No first-site-proximal rabbit deletion was detected in the current alignment.")
    write_text(OUTPUTS / "deletion_summary.txt", text, summary)
    save_summary(summary)
    print(text)


if __name__ == "__main__":
    main()
