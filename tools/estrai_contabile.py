#!/usr/bin/env python3
"""Extract the data fields of a FinecoBank "contabile bonifico" PDF into an editable record.

The PDF itself is a locked, bank-issued confirmation: it is treated here strictly as a
*read-only source*. This tool copies its values into plain JSON/CSV so they can be
corrected, classified and reconciled — it never rewrites, re-renders or reproduces the
bank document, its letterhead or its signature.

Usage:
    python3 tools/estrai_contabile.py docs/contabile_bonifico_3398064328.pdf -o data/contabile_bonifico_3398064328.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from pypdf import PdfReader
except ModuleNotFoundError:  # pragma: no cover
    sys.exit("pypdf is required: pip install pypdf")

# Fineco field name -> (record key, kind)
FIELD_MAP: dict[str, tuple[str, str]] = {
    "gg/mm/aaaa": ("data_stampa", "date"),
    "importoEuro": ("importo_interi", "text"),
    "importoEuro_1": ("importo_centesimi", "text"),
    "DataAccredito": ("data_accredito", "date"),
    "ValutaAddebitoOrdinante": ("data_valuta_addebito", "date"),
    "Causale": ("causale", "text"),
    "Commissioni_Spesa": ("commissioni_spese", "text"),
    "CodiceRIF": ("trn", "text"),
    "Motivazione": ("motivazione_pagamento", "text"),
    "Cat_Pagamento": ("categoria_pagamento", "text"),
    "Nome_Cognome_Ordinante": ("ordinante_nome", "text"),
    "IBAN_Ordinante": ("ordinante_iban", "text"),
    "RIF_Ordinante": ("ordinante_riferimento", "text"),
    "EFF_Ordinante": ("ordinante_effettivo", "text"),
    "RIF_Ordinante_EFF": ("ordinante_effettivo_riferimento", "text"),
    "Nome_Cognome_Beneficiario": ("beneficiario_nome", "text"),
    "IND_Beneficiario": ("beneficiario_indirizzo", "text"),
    "Banca_Beneficiario": ("beneficiario_banca", "text"),
    "IBAN_Beneficiario": ("beneficiario_iban", "text"),
    "BIC_Beneficiario": ("beneficiario_bic", "text"),
    "RIF_Beneficiario": ("beneficiario_riferimento", "text"),
    "EFF_Beneficiario": ("beneficiario_effettivo", "text"),
    "RIF_Beneficiario_EFF": ("beneficiario_effettivo_riferimento", "text"),
    "DA_Disposizione": ("canale_disposizione", "text"),
    "dataOperazione": ("data_disposizione", "date"),
    "oraOperazione": ("ora_disposizione", "time"),
}

# Fields the record adds on top of the document, so the row is editable/classifiable.
EDITABLE_DEFAULTS = {
    "note": "",
    "categoria": "",
    "riconciliato": False,
    "riconciliato_con": None,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def iban_mod97_ok(iban: str) -> bool:
    """Validate an IBAN with the ISO 13616 mod-97 check (1 == valid)."""
    flat = "".join(iban.split()).upper()
    if len(flat) < 5 or not flat[:2].isalpha() or not flat[2:4].isdigit():
        return False
    rearranged = flat[4:] + flat[:4]
    try:
        return int("".join(str(int(ch, 36)) for ch in rearranged)) % 97 == 1
    except ValueError:
        return False


def to_iso_date(value: str) -> str | None:
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def to_iso_time(value: str) -> str | None:
    value = (value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time().isoformat()
        except ValueError:
            continue
    return None


def extract(pdf_path: Path) -> dict:
    reader = PdfReader(str(pdf_path))
    raw_fields = reader.get_fields() or {}
    values = {name: spec.get("/V") for name, spec in raw_fields.items()}

    record: dict = {}
    for field, (key, kind) in FIELD_MAP.items():
        raw = values.get(field)
        if raw in (None, ""):
            continue
        raw = str(raw).strip()
        if kind == "date":
            record[key] = to_iso_date(raw) or raw
        elif kind == "time":
            record[key] = to_iso_time(raw) or raw
        else:
            record[key] = raw

    # Amount is split across two widgets on the Fineco form.
    if "importo_interi" in record or "importo_centesimi" in record:
        ints_ = (record.pop("importo_interi", "") or "").replace(".", "").replace(" ", "")
        cents = (record.pop("importo_centesimi", "") or "").strip() or "0"
        try:
            record["importo_eur"] = f"{int(ints_ or 0)}.{int(cents):02d}"
        except ValueError:
            record["importo_eur"] = f"{ints_}.{cents}"

    for key in ("ordinante_iban", "beneficiario_iban"):
        if key in record:
            record[key] = "".join(record[key].split()).upper()

    record.update(EDITABLE_DEFAULTS)

    strapped = {
        "documento": {
            "file_name": pdf_path.name,
            "sha256": sha256(pdf_path),
            "pagine": len(reader.pages),
            "banca": "FinecoBank S.p.A.",
            "tipo": "contabile_bonifico_sepa",
            "estratto_il": date.today().isoformat(),
            "nota": (
                "Copia non modificata del documento originale della banca. "
                "Fonte di riferimento: il PDF, non questo record."
            ),
        },
        "verifiche": {
            "ordinante_iban_valido": iban_mod97_ok(record.get("ordinante_iban", "")),
            "beneficiario_iban_valido": iban_mod97_ok(record.get("beneficiario_iban", "")),
        },
        "campi_non_mappati": {
            name: str(value) for name, value in values.items() if name not in FIELD_MAP and value
        },
    }

    ordered = {
        "riferimento": record.get("trn"),
        **record,
        **strapped,
    }
    return ordered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="output .json (default: stdout)")
    parser.add_argument("--csv", type=Path, help="also write a flat .csv row")
    args = parser.parse_args()

    record = extract(args.pdf)
    payload = json.dumps(record, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
        print(f"scritto {args.out}", file=sys.stderr)
    else:
        print(payload)

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        flat = {
            k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list, bool)) else v)
            for k, v in record.items()
        }
        with args.csv.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(flat))
            writer.writeheader()
            writer.writerow(flat)
        print(f"scritto {args.csv}", file=sys.stderr)


if __name__ == "__main__":
    main()
