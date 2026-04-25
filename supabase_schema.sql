-- Scaler AI Agent — Supabase schema
-- Run this in the Supabase SQL editor.

CREATE TABLE IF NOT EXISTS sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  evaluator_phone TEXT NOT NULL,
  bda_phone TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  company TEXT,
  experience_years INTEGER,
  role TEXT,
  intent TEXT,
  linkedin_summary TEXT,
  persona_type TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS generated_content (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  content_type TEXT NOT NULL,                 -- 'nudge' | 'pdf'
  transcript TEXT,
  extracted_questions JSONB,
  nudge_text TEXT,
  pdf_url TEXT,
  cover_message TEXT,
  approval_status TEXT DEFAULT 'pending',     -- 'pending' | 'approved' | 'edited' | 'skipped'
  edited_cover_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Public bucket for PDFs (Twilio needs a public URL to attach media).
INSERT INTO storage.buckets (id, name, public)
VALUES ('pdfs', 'pdfs', true)
ON CONFLICT (id) DO NOTHING;

-- Allow anon role to upload to and read from the pdfs bucket.
-- (Bucket-level public=true exposes objects via public URL but does NOT
-- bypass storage.objects RLS for INSERT — the policy below does.)
CREATE POLICY "anon_pdfs_insert" ON storage.objects
  FOR INSERT TO anon WITH CHECK (bucket_id = 'pdfs');
CREATE POLICY "anon_pdfs_select" ON storage.objects
  FOR SELECT TO anon USING (bucket_id = 'pdfs');
CREATE POLICY "anon_pdfs_update" ON storage.objects
  FOR UPDATE TO anon USING (bucket_id = 'pdfs');

-- Disable RLS on app tables (MVP — replace with proper policies for production).
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE leads DISABLE ROW LEVEL SECURITY;
ALTER TABLE generated_content DISABLE ROW LEVEL SECURITY;
