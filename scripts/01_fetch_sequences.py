from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from urllib.parse import quote

import requests
from Bio import SeqIO

from common import DATA, add_generated, add_warning, load_summary, remove_generated, save_summary, validate_nonempty, write_text


HUMAN_ACCESSION = "P00734"
UNIPROT_FASTA = "https://rest.uniprot.org/uniprotkb/{accession}.fasta"
UNIPROT_SEARCH = "https://rest.uniprot.org/uniprotkb/search"
SEARCH_TERMS = [
    "organism_id:9986 AND gene:F2",
    '"Oryctolagus cuniculus" prothrombin',
    '"Oryctolagus cuniculus" "coagulation factor II"',
]
NCBI_SEARCH_TERMS = [
    '"Oryctolagus cuniculus"[Organism] AND prothrombin[Protein Name]',
    '"Oryctolagus cuniculus"[Organism] AND "coagulation factor II"',
    '"Oryctolagus cuniculus"[Organism] AND F2[Gene Name]',
]
NCBI_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def request_text(url: str, **kwargs: object) -> str:
    response = requests.get(url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.text


def request_json(url: str, **kwargs: object) -> dict:
    response = requests.get(url, timeout=30, **kwargs)
    response.raise_for_status()
    return response.json()


def fetch_human(summary: dict) -> None:
    path = DATA / "sequences" / "human_P00734.fasta"
    fasta = request_text(UNIPROT_FASTA.format(accession=HUMAN_ACCESSION))
    if not fasta.strip().startswith(">"):
        raise ValueError("UniProt did not return FASTA for human P00734")
    write_text(path, fasta, summary)
    validate_nonempty(path, "Human FASTA")


def candidate_from_result(result: dict) -> dict:
    protein = result.get("proteinDescription", {})
    recommended = protein.get("recommendedName", {})
    protein_name = recommended.get("fullName", {}).get("value", "")
    if not protein_name:
        protein_name = "; ".join(
            item.get("fullName", {}).get("value", "")
            for item in protein.get("submissionNames", [])
            if item.get("fullName", {}).get("value")
        )
    genes = [
        gene.get("geneName", {}).get("value", "")
        for gene in result.get("genes", [])
        if gene.get("geneName", {}).get("value")
    ]
    organism = result.get("organism", {})
    return {
        "accession": result.get("primaryAccession"),
        "entry_name": result.get("uniProtkbId"),
        "protein_name": protein_name,
        "genes": genes,
        "organism_name": organism.get("scientificName"),
        "organism_id": organism.get("taxonId"),
        "reviewed": result.get("entryType", "").lower().startswith("swiss-prot"),
        "sequence": result.get("sequence", {}).get("value", ""),
        "sequence_length": result.get("sequence", {}).get("length"),
    }


def is_good_rabbit_f2(candidate: dict) -> bool:
    protein = candidate.get("protein_name", "").lower()
    genes = {gene.upper() for gene in candidate.get("genes", [])}
    seq = candidate.get("sequence", "")
    return (
        candidate.get("organism_id") == 9986
        and 450 <= len(seq) <= 700
        and ("F2" in genes or "prothrombin" in protein or "coagulation factor ii" in protein)
    )


def search_rabbit(summary: dict) -> list[dict]:
    raw: dict[str, dict] = {}
    candidates: dict[str, dict] = {}
    fields = "accession,id,protein_name,gene_names,organism_id,organism_name,sequence,reviewed"
    for term in SEARCH_TERMS:
        url = f"{UNIPROT_SEARCH}?query={quote(term)}&format=json&fields={fields}&size=25"
        try:
            payload = request_json(url)
        except Exception as exc:  # noqa: BLE001 - record external-resource failures clearly.
            add_warning(summary, f"Rabbit UniProt search failed for {term!r}: {exc}")
            raw[term] = {"error": str(exc)}
            continue
        raw[term] = payload
        for result in payload.get("results", []):
            candidate = candidate_from_result(result)
            accession = candidate.get("accession")
            if accession and is_good_rabbit_f2(candidate):
                candidates[accession] = candidate
    raw_path = DATA / "raw" / "uniprot_search_rabbit.json"
    write_text(raw_path, json.dumps(raw, indent=2) + "\n", summary)
    return list(candidates.values())


def write_candidate_fasta(path: Path, candidate: dict) -> None:
    header = (
        f">{candidate['accession']}|{candidate.get('entry_name', '')} "
        f"{candidate.get('protein_name', 'rabbit prothrombin')} "
        f"OS={candidate.get('organism_name', 'Oryctolagus cuniculus')} "
        f"OX={candidate.get('organism_id', '')}"
    )
    path.write_text(header.rstrip() + "\n" + candidate["sequence"] + "\n")


def search_ncbi_rabbit(summary: dict) -> list[dict]:
    raw: dict[str, dict] = {}
    candidates: dict[str, dict] = {}
    for term in NCBI_SEARCH_TERMS:
        try:
            search = request_json(
                f"{NCBI_EUTILS}/esearch.fcgi",
                params={"db": "protein", "term": term, "retmode": "json", "retmax": 10},
            )
            ids = search.get("esearchresult", {}).get("idlist", [])
            summary_payload = {}
            if ids:
                summary_payload = request_json(
                    f"{NCBI_EUTILS}/esummary.fcgi",
                    params={"db": "protein", "id": ",".join(ids), "retmode": "json"},
                )
                fasta = request_text(
                    f"{NCBI_EUTILS}/efetch.fcgi",
                    params={"db": "protein", "id": ",".join(ids), "rettype": "fasta", "retmode": "text"},
                )
            else:
                fasta = ""
            raw[term] = {"search": search, "summary": summary_payload, "fasta": fasta}
        except Exception as exc:  # noqa: BLE001 - external-resource failure is recorded.
            add_warning(summary, f"Rabbit NCBI Protein search failed for {term!r}: {exc}")
            raw[term] = {"error": str(exc)}
            continue

        for record in SeqIO.parse(StringIO(fasta), "fasta"):
            description = record.description.lower()
            sequence = str(record.seq)
            if (
                "oryctolagus cuniculus" in description
                and ("prothrombin" in description or "coagulation factor ii" in description)
                and 450 <= len(sequence) <= 700
            ):
                accession = record.id.split(".")[0]
                candidates[record.id] = {
                    "accession": record.id,
                    "entry_name": record.id,
                    "protein_name": record.description,
                    "genes": ["F2"] if "f2" in description else [],
                    "organism_name": "Oryctolagus cuniculus",
                    "organism_id": 9986,
                    "reviewed": False,
                    "sequence": sequence,
                    "sequence_length": len(sequence),
                    "source": "NCBI Protein",
                    "accession_base": accession,
                }
    raw_path = DATA / "raw" / "ncbi_search_rabbit.json"
    write_text(raw_path, json.dumps(raw, indent=2) + "\n", summary)
    return list(candidates.values())

def resolve_rabbit(summary: dict) -> None:
    candidates = search_rabbit(summary)
    source = "UniProt"
    if not candidates:
        candidates = search_ncbi_rabbit(summary)
        source = "NCBI Protein"
    rabbit_path = DATA / "sequences" / "rabbit_F2.fasta"
    if len(candidates) == 1:
        write_candidate_fasta(rabbit_path, candidates[0])
        add_generated(summary, rabbit_path)
        stale_not_found = DATA / "sequences" / "rabbit_NOT_FOUND.txt"
        if stale_not_found.exists():
            stale_not_found.unlink()
            remove_generated(summary, stale_not_found)
        summary["rabbit_accession"] = candidates[0]["accession"]
        summary["rabbit_sequence_status"] = "resolved"
        summary["rabbit_sequence_source"] = source
        return

    if len(candidates) > 1:
        candidates_path = DATA / "sequences" / "rabbit_candidates.fasta"
        text = ""
        for candidate in candidates:
            header = (
                f">{candidate['accession']}|{candidate.get('entry_name', '')} "
                f"{candidate.get('protein_name', '')} reviewed={candidate.get('reviewed')} "
                f"length={candidate.get('sequence_length')}"
            )
            text += header.rstrip() + "\n" + candidate["sequence"] + "\n"
        write_text(candidates_path, text, summary)
        add_warning(
            summary,
            f"Multiple plausible rabbit F2/prothrombin {source} candidates found; "
            "review data/sequences/rabbit_candidates.fasta and copy the chosen record to rabbit_F2.fasta.",
        )
        summary["rabbit_sequence_status"] = "multiple_candidates"
        summary["rabbit_sequence_source"] = source
        return

    not_found = DATA / "sequences" / "rabbit_NOT_FOUND.txt"
    write_text(
        not_found,
        "No unambiguous Oryctolagus cuniculus F2/prothrombin sequence was found through UniProt REST searches.\n"
        "Manually paste the rabbit F2/prothrombin FASTA into data/sequences/rabbit_F2.fasta, then rerun scripts 02-06.\n"
        "Do not invent an accession; record the source in outputs/run_summary.json or README notes.\n",
        summary,
    )
    add_warning(summary, "Rabbit F2/prothrombin sequence was not resolved from UniProt.")
    summary["rabbit_sequence_status"] = "not_found"


def main() -> None:
    summary = load_summary()
    try:
        fetch_human(summary)
    except Exception as exc:  # noqa: BLE001
        add_warning(summary, f"Human P00734 FASTA fetch failed: {exc}")
        raise
    resolve_rabbit(summary)

    human_path = DATA / "sequences" / "human_P00734.fasta"
    records = list(SeqIO.parse(human_path, "fasta"))
    if not records or len(records[0].seq) == 0:
        raise ValueError("Human FASTA validation failed: no sequence record")
    save_summary(summary)
    print(f"Wrote {human_path}")
    print(f"Rabbit sequence status: {summary['rabbit_sequence_status']}")


if __name__ == "__main__":
    main()
