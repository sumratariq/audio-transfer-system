-- Run this once in the Supabase SQL editor (Project → SQL Editor → New query)

create table if not exists audio_files (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    storage_path text not null,
    content_type text,
    size_bytes bigint,
    uploaded_at timestamptz not null default now()
);

-- Optional but recommended: enable Row Level Security.
-- Since the server talks to Supabase with the service_role key (not the
-- anon key), it bypasses RLS automatically, so this keeps the table
-- locked down to any other client that only has the anon key.
alter table audio_files enable row level security;