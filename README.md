# rea — contabili di bonifico

Transcript of the FinecoBank payment confirmation in `docs/`, stored as **editable data**
instead of an editable document.

## Why not an editable PDF

`docs/contabile_bonifico_3398064328.pdf` is a bank-issued confirmation of payment: its
form fields are locked (`ReadOnly`), it carries Fineco's letterhead and the signature of
the bank's managing director, and it is stamped *"Rilasciata per gli usi consentiti dalla
legge"*. An unlocked or rebuilt copy of that document is a fill-in-the-blank proof of
payment, so this repository does not produce one. The extraction here takes the **values**
out of the PDF; the PDF stays untouched and remains the only valid document.

## What the record says

| campo | valore |
| --- | --- |
| TRN | `2611023398064328480320055700IT` |
| Importo | € 2.300,00 |
| Data accredito / valuta addebito | 03/11/2026 / 03/11/2026 |
| Disposizione | 02/11/2026 alle 13:16 — Internet Banking |
| Causale | giroconto |
| Ordinante | PASQUALE PIER LUIGI — `IT66C0301503200000005050889` |
| Beneficiario | MARIA TERESA LONARDI — `IT78S0301503200000005050855` |
| Banca beneficiario | FINECOBANK SPA — BIC `FEBIITM1XXX` |
| Commissioni | nessuna |
| Stampa documento | 04/11/2026 |

Both IBANs pass the ISO 13616 mod-97 check (see `verifiche` in the JSON).

## Files

```
docs/contabile_bonifico_3398064328.pdf        original, unmodified (sha256 325467ba…bb80c4f)
data/contabile_bonifico_3398064328.json       editable record
data/contabile_bonifico_3398064328.csv        same record as a flat row
tools/estrai_contabile.py                     PDF -> JSON/CSV extractor
supabase/migrations/20261120120000_contabili_bonifico.sql
supabase/seed/20261120120000_contabili_bonifico_seed.sql
```

## Where it lives

Table **`traccia.contabili_bonifico`** (project ref `mmjycpdfjlbckeefbtuq`), one row with
`trn = 2611023398064328480320055700IT`. RLS is on with no policies, same convention as the
rest of the `traccia` schema, so it is reachable with the **service role** only.

Editable by hand in the Supabase Table Editor: `categoria`, `note`, `riconciliato`,
`riconciliato_con`, `campi_extra`. The extracted fields can also be corrected there — with
the caveat that the corrected row then describes the payment, it does not represent it.

```sql
-- example: classify and reconcile
update traccia.contabili_bonifico
   set categoria = 'giroconto interno',
       riconciliato = true,
       riconciliato_con = '<traccia.bank_transfers.id>'
 where trn = '2611023398064328480320055700IT';
```

## Adding another contabile

```bash
pip install pypdf
python3 tools/estrai_contabile.py nuovo_contabile.pdf \
        -o data/nuovo_contabile.json --csv data/nuovo_contabile.csv
```

The extractor maps the Fineco AcroForm field names, normalises dates to ISO and the amount
to a single decimal value, validates both IBANs and keeps any unmapped field in
`campi_non_mappati` so nothing silently disappears. It only reads the PDF.

## Scope

This is bookkeeping: a searchable, correctable copy of numbers you already hold. It is not
a document generator — no PDF, letterhead, signature or bank form is produced here, and the
table should not be used to evidence a payment. If a contabile contains a mistake, the
document to rely on is the one the bank reissues.
