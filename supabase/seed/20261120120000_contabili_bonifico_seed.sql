-- Seed: contabile di bonifico 2611023398064328480320055700IT
-- Dati estratti da docs/contabile_bonifico_3398064328.pdf (sha256 325467ba...bb80c4f).
-- Idempotente: si può rilanciare senza duplicare (unique su trn).

insert into traccia.contabili_bonifico (
    trn,
    banca,
    tipo_documento,
    importo_eur,
    data_accredito,
    data_valuta_addebito,
    data_stampa,
    data_disposizione,
    ora_disposizione,
    causale,
    commissioni_spese,
    canale_disposizione,
    ordinante_nome,
    ordinante_iban,
    beneficiario_nome,
    beneficiario_iban,
    beneficiario_banca,
    beneficiario_bic,
    documento_file_name,
    documento_sha256,
    documento_path,
    verifiche,
    campi_extra
) values (
    '2611023398064328480320055700IT',
    'FinecoBank S.p.A.',
    'contabile_bonifico_sepa',
    2300.00,
    date '2026-11-03',
    date '2026-11-03',
    date '2026-11-04',
    date '2026-11-02',
    time '13:16',
    'giroconto',
    'nessuna',
    'Internet Banking',
    'PASQUALE PIER LUIGI',
    'IT66C0301503200000005050889',
    'MARIA TERESA LONARDI',
    'IT78S0301503200000005050855',
    'FINECOBANK SPA',
    'FEBIITM1XXX',
    'contabile_bonifico_3398064328.pdf',
    '325467ba2806ece02dba44ed96e69e1a5070f079f6773ec7b89adb6d5bb80c4f',
    'docs/contabile_bonifico_3398064328.pdf',
    jsonb_build_object(
        'ordinante_iban_valido', true,
        'beneficiario_iban_valido', true
    ),
    '{}'::jsonb
)
on conflict (trn) do nothing;
