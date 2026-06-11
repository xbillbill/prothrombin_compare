from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests
from Bio import SeqIO
from Bio.PDB import PDBParser

from common import DATA, add_generated, add_warning, load_summary, save_summary, validate_nonempty, write_text


HUMAN_ACCESSION = "P00734"
AF_URL = "https://alphafold.ebi.ac.uk/files/AF-{accession}-F1-model_v4.pdb"
AF_API = "https://alphafold.ebi.ac.uk/api/prediction/{accession}"
AA3 = {
    "A": "ALA",
    "R": "ARG",
    "N": "ASN",
    "D": "ASP",
    "C": "CYS",
    "Q": "GLN",
    "E": "GLU",
    "G": "GLY",
    "H": "HIS",
    "I": "ILE",
    "L": "LEU",
    "K": "LYS",
    "M": "MET",
    "F": "PHE",
    "P": "PRO",
    "S": "SER",
    "T": "THR",
    "W": "TRP",
    "Y": "TYR",
    "V": "VAL",
}
BACKBONE_ATOMS = {"N", "CA", "C", "O"}


def alphafold_urls(accession: str) -> list[str]:
    urls = []
    try:
        response = requests.get(AF_API.format(accession=accession), timeout=45)
        if response.status_code == 200:
            payload = response.json()
            for item in payload:
                pdb_url = item.get("pdbUrl")
                if pdb_url:
                    urls.append(pdb_url)
                latest = item.get("latestVersion")
                if latest:
                    urls.append(f"https://alphafold.ebi.ac.uk/files/AF-{accession}-F1-model_v{latest}.pdb")
    except Exception:
        pass
    urls.extend(
        f"https://alphafold.ebi.ac.uk/files/AF-{accession}-F1-model_v{version}.pdb"
        for version in range(6, 0, -1)
    )
    deduped = []
    for url in urls:
        if url not in deduped:
            deduped.append(url)
    return deduped


def download_pdb(accession: str, path: Path) -> str | None:
    for url in alphafold_urls(accession):
        response = requests.get(url, timeout=45)
        if response.status_code == 200 and response.text.startswith(("HEADER", "MODEL", "ATOM")):
            path.write_text(response.text)
            if path.stat().st_size > 0:
                return url
    return None


def parse_accession_from_fasta(path: Path) -> str | None:
    if not path.exists():
        return None
    record = next(SeqIO.parse(path, "fasta"), None)
    if record is None:
        return None
    token = record.id.split("|")[0]
    return token or None


def write_colabfold_files(summary: dict) -> None:
    rabbit_fasta = DATA / "sequences" / "rabbit_F2.fasta"
    if rabbit_fasta.exists():
        fasta_text = rabbit_fasta.read_text()
        colab_path = DATA / "structures" / "rabbit_colabfold_input.fasta"
        write_text(colab_path, fasta_text, summary)
    else:
        colab_path = None
        add_warning(summary, "Cannot create rabbit ColabFold FASTA because rabbit_F2.fasta is missing.")
    instructions = DATA / "structures" / "RUN_COLABFOLD_INSTRUCTIONS.md"
    write_text(
        instructions,
        "# Rabbit prothrombin ColabFold instructions\n\n"
        "Rabbit AlphaFold DB model was not available or could not be downloaded.\n\n"
        "1. Run ColabFold on `data/structures/rabbit_colabfold_input.fasta`.\n"
        "2. Save the final ranked model as `data/structures/rabbit_colabfold_model.pdb`.\n"
        "3. Re-run:\n\n"
        "```bash\n"
        "python scripts/04_analyze_cleavage_region.py\n"
        "python scripts/05_make_pymol_script.py\n"
        "python scripts/06_make_report.py\n"
        "```\n\n"
        "Use the model as a structural hypothesis only; activation kinetics require biochemical validation.\n",
        summary,
    )
    if colab_path:
        print(f"Prepared {colab_path}")


def format_atom_line(
    serial: int,
    atom_name: str,
    resname: str,
    chain_id: str,
    resseq: int,
    x: float,
    y: float,
    z: float,
    occupancy: float,
    bfactor: float,
    element: str,
) -> str:
    return (
        f"ATOM  {serial:5d} {atom_name:<4}{resname:>3} {chain_id}{resseq:4d}    "
        f"{x:8.3f}{y:8.3f}{z:8.3f}{occupancy:6.2f}{bfactor:6.2f}          {element:>2}"
    )


def create_threaded_rabbit_pdb(summary: dict) -> Path | None:
    human_pdb = DATA / "structures" / "human_AF_P00734.pdb"
    alignment_csv = DATA / "alignments" / "human_rabbit_global_alignment.csv"
    rabbit_fasta = DATA / "sequences" / "rabbit_F2.fasta"
    if not human_pdb.exists() or not alignment_csv.exists() or not rabbit_fasta.exists():
        add_warning(
            summary,
            "Cannot create threaded rabbit PDB because human PDB, rabbit FASTA, or alignment CSV is missing.",
        )
        return None

    rows = pd.read_csv(alignment_csv)
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("human_AF_P00734", human_pdb)
    chain = next(structure.get_chains())
    human_residues = {
        int(residue.id[1]): residue
        for residue in chain
        if residue.id[0] == " " and any(atom.name in BACKBONE_ATOMS for atom in residue)
    }
    output = DATA / "structures" / "rabbit_threaded_from_human_AF_P00734.pdb"
    fasta_record = next(SeqIO.parse(rabbit_fasta, "fasta"), None)
    rabbit_accession = fasta_record.id if fasta_record else summary.get("rabbit_accession", "unknown")

    lines = [
        "HEADER    HOMOLOGY-THREADED RABBIT PROTHROMBIN VISUALIZATION MODEL",
        "TITLE     RABBIT PROTHROMBIN BACKBONE THREADED FROM HUMAN ALPHAFOLD P00734",
        "REMARK   1 THIS IS NOT AN EXPERIMENTAL STRUCTURE.",
        "REMARK   2 THIS IS NOT A DE NOVO ALPHAFOLD/COLABFOLD PREDICTION.",
        "REMARK   3 RABBIT SEQUENCE IS THREADED ONTO THE HUMAN ALPHAFOLD BACKBONE USING THE SAVED ALIGNMENT.",
        "REMARK   4 BACKBONE ATOMS N, CA, C, O ARE COPIED WHERE HUMAN AND RABBIT RESIDUES ALIGN.",
        "REMARK   5 HUMAN DELETION-EQUIVALENT POSITIONS 299-303 ARE ABSENT IN RABBIT BY ALIGNMENT.",
        "REMARK   6 USE THIS MODEL FOR VISUALIZING RESIDUE MAPPING ONLY; DO NOT INTERPRET RMSD AS INDEPENDENT STRUCTURAL EVIDENCE.",
        f"REMARK   7 RABBIT SEQUENCE SOURCE: {rabbit_accession}",
    ]
    serial = 1
    modeled = 0
    skipped = 0
    for row in rows.itertuples(index=False):
        human_pos = getattr(row, "human_pos")
        rabbit_pos = getattr(row, "rabbit_pos")
        rabbit_aa = getattr(row, "rabbit_aa")
        if pd.isna(human_pos) or pd.isna(rabbit_pos) or rabbit_aa == "-":
            skipped += 1
            continue
        human_pos = int(human_pos)
        rabbit_pos = int(rabbit_pos)
        residue = human_residues.get(human_pos)
        resname = AA3.get(str(rabbit_aa), "UNK")
        if residue is None:
            skipped += 1
            continue
        wrote_residue = False
        for atom_name in ["N", "CA", "C", "O"]:
            if atom_name not in residue:
                continue
            atom = residue[atom_name]
            x, y, z = (float(value) for value in atom.coord)
            lines.append(
                format_atom_line(
                    serial,
                    atom_name,
                    resname,
                    "R",
                    rabbit_pos,
                    x,
                    y,
                    z,
                    float(atom.occupancy or 1.0),
                    float(atom.bfactor or 0.0),
                    atom.element.strip() or atom_name[0],
                )
            )
            serial += 1
            wrote_residue = True
        if wrote_residue:
            modeled += 1
    lines.extend(["TER", "END"])
    write_text(output, "\n".join(lines) + "\n", summary)
    summary.setdefault("structure_sources", {})["rabbit_threaded_proxy"] = {
        "source": "Human AlphaFold backbone threaded with rabbit sequence",
        "path": "data/structures/rabbit_threaded_from_human_AF_P00734.pdb",
        "rabbit_accession": summary.get("rabbit_accession"),
        "modeled_rabbit_residues": modeled,
        "skipped_alignment_rows": skipped,
        "valid_for": "visual residue mapping and deletion-region rendering",
        "not_valid_for": "independent RMSD, kinetics, or prothrombinase mechanism proof",
    }
    print(f"Created threaded rabbit visualization PDB with {modeled} residues: {output}")
    return output


def main() -> None:
    summary = load_summary()
    structures = summary.setdefault("structure_sources", {})

    human_path = DATA / "structures" / "human_AF_P00734.pdb"
    try:
        human_url = download_pdb(HUMAN_ACCESSION, human_path)
        if human_url:
            add_generated(summary, human_path)
            structures["human"] = {
                "source": "AlphaFold DB",
                "accession": HUMAN_ACCESSION,
                "url": human_url,
                "path": "data/structures/human_AF_P00734.pdb",
            }
            validate_nonempty(human_path, "Human AlphaFold PDB")
        else:
            add_warning(summary, "Human AlphaFold DB PDB could not be downloaded.")
    except Exception as exc:  # noqa: BLE001
        add_warning(summary, f"Human AlphaFold DB PDB download failed: {exc}")

    rabbit_accession = summary.get("rabbit_accession") or parse_accession_from_fasta(DATA / "sequences" / "rabbit_F2.fasta")
    if rabbit_accession:
        summary["rabbit_accession"] = rabbit_accession
        local_rabbit_model = DATA / "structures" / "rabbit_AF_model.pdb"
        if local_rabbit_model.exists() and local_rabbit_model.stat().st_size > 0:
            structures["rabbit"] = {
                "source": "AlphaFold website prediction imported locally",
                "accession": rabbit_accession,
                "path": "data/structures/rabbit_AF_model.pdb",
                "aligned_path": "data/structures/rabbit_aligned_to_human.pdb",
            }
            add_generated(summary, local_rabbit_model)
            validate_nonempty(local_rabbit_model, "Rabbit AlphaFold PDB")
            print(f"Using existing rabbit AlphaFold model at {local_rabbit_model}")
            save_summary(summary)
            print("Structure fetch/preparation complete.")
            return
        rabbit_path = DATA / "structures" / "rabbit_AF_model.pdb"
        try:
            rabbit_url = download_pdb(rabbit_accession, rabbit_path)
            if rabbit_url:
                add_generated(summary, rabbit_path)
                structures["rabbit"] = {
                    "source": "AlphaFold DB",
                    "accession": rabbit_accession,
                    "url": rabbit_url,
                    "path": "data/structures/rabbit_AF_model.pdb",
                    "aligned_path": "data/structures/rabbit_aligned_to_human.pdb",
                }
                print(f"Downloaded rabbit AlphaFold model for {rabbit_accession}")
            else:
                structures["rabbit"] = {
                    "source": "Threaded proxy created; ColabFold recommended for independent model",
                    "accession": rabbit_accession,
                    "path": "data/structures/rabbit_threaded_from_human_AF_P00734.pdb",
                    "fallback_colabfold_path": "data/structures/rabbit_colabfold_model.pdb",
                    "aligned_path": "data/structures/rabbit_aligned_to_human.pdb",
                }
                add_warning(summary, f"No AlphaFold DB model was available for rabbit accession {rabbit_accession}.")
                write_colabfold_files(summary)
                create_threaded_rabbit_pdb(summary)
        except Exception as exc:  # noqa: BLE001
            add_warning(summary, f"Rabbit AlphaFold DB PDB download failed for {rabbit_accession}: {exc}")
            write_colabfold_files(summary)
            create_threaded_rabbit_pdb(summary)
    else:
        add_warning(summary, "Rabbit accession unresolved; skipping rabbit AlphaFold DB lookup.")
        write_colabfold_files(summary)

    save_summary(summary)
    print("Structure fetch/preparation complete.")


if __name__ == "__main__":
    main()
