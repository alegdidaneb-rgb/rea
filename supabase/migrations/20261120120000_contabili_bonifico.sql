-- Contabili di bonifico: i dati del documento bancario come record modificabile.
--
-- Il PDF originale resta l'unica fonte probatoria (vedi documento_sha256 /
-- documento_path): questa tabella contiene una copia *di lavoro* dei valori, da
-- correggere, classificare e riconciliare. Non serve a rigenerare il documento
-- della banca e non va usata come prova di pagamento.

create table if not exists traccia.contabili_bonifico (
    id                     uuid primary key default gen_random_uuid(),
    trn                    text not null unique,
    banca                  text not null default 'FinecoBank S.p.A.',
    tipo_documento         text not null default 'contabile_bonifico_sepa',

    importo_eur            numeric(14, 2) not null check (importo_eur > 0),
    data_accredito         date,
    data_valuta_addebito   date,
    data_stampa            date,
    data_disposizione      date,
    ora_disposizione       time without time zone,

    causale                text,
    commissioni_spese      text,
    canale_disposizione    text,

    ordinante_nome         text not null,
    ordinante_iban         text not null,

    beneficiario_nome      text not null,
    beneficiario_iban      text not null,
    beneficiario_banca     text,
    beneficiario_bic       text,

    documento_file_name    text,
    documento_sha256       text,
    documento_path         text,
    verifiche              jsonb not null default '{}'::jsonb,
    campi_extra            jsonb not null default '{}'::jsonb,

    -- campi liberi: sono questi che si modificano a mano
    categoria              text not null default '',
    note                   text not null default '',
    riconciliato           boolean not null default false,
    riconciliato_con       uuid,

    creato_il              timestamptz not null default now(),
    aggiornato_il          timestamptz not null default now()
);

comment on table traccia.contabili_bonifico is
    'Dati estratti dai contabili di bonifico (record di lavoro modificabile). Il PDF originale è la fonte probatoria.';
comment on column traccia.contabili_bonifico.trn is
    'Codice riferimento (TRN) del bonifico: chiave naturale, evita duplicati in import.';
comment on column traccia.contabili_bonifico.riconciliato_con is
    'Collega il contabile alla riga di riconciliazione (es. traccia.bank_transfers.id).';

create index if not exists contabili_bonifico_beneficiario_iban_idx
    on traccia.contabili_bonifico (beneficiario_iban);
create index if not exists contabili_bonifico_data_accredito_idx
    on traccia.contabili_bonifico (data_accredito desc);
create index if not exists contabili_bonifico_riconciliato_idx
    on traccia.contabili_bonifico (riconciliato)
    where riconciliato = false;

create or replace function traccia.tg_contabili_bonifico_aggiornato_il()
returns trigger
language plpgsql
as $$
begin
    new.aggiornato_il := now();
    return new;
end;
$$;

drop trigger if exists contabili_bonifico_aggiornato_il on traccia.contabili_bonifico;
create trigger contabili_bonifico_aggiornato_il
    before update on traccia.contabili_bonifico
    for each row
    execute function traccia.tg_contabili_bonifico_aggiornato_il();

-- Stessa convenzione del resto dello schema traccia: RLS attiva, nessuna policy,
-- quindi accesso solo con service role (le API pubbliche non vedono la tabella).
alter table traccia.contabili_bonifico enable row level security;

revoke all on traccia.contabili_bonifico from anon, authenticated;
grant select, insert, update, delete on traccia.contabili_bonifico to service_role;
