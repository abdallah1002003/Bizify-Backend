-- Migration: Add Arabic/English language support
-- Run this in Supabase SQL Editor

-- 1. Add preferred_language to user_profiles
ALTER TABLE user_profiles
    ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(2) NOT NULL DEFAULT 'en';

-- 2. Add language to ideas
ALTER TABLE ideas
    ADD COLUMN IF NOT EXISTS language VARCHAR(2) NOT NULL DEFAULT 'en';

-- 3. Create idea_translations table
CREATE TABLE IF NOT EXISTS idea_translations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idea_id     UUID NOT NULL REFERENCES ideas(id) ON DELETE CASCADE,
    language    VARCHAR(2) NOT NULL,
    section_name VARCHAR NOT NULL,
    content     TEXT NOT NULL,
    translated_at TIMESTAMPTZ DEFAULT now(),
    model_used  VARCHAR
);

-- Index for fast lookup by idea + language
CREATE INDEX IF NOT EXISTS ix_idea_translations_idea_lang
    ON idea_translations (idea_id, language);

-- Unique constraint: one row per (idea, language, section)
ALTER TABLE idea_translations
    DROP CONSTRAINT IF EXISTS uq_idea_translation_section;

ALTER TABLE idea_translations
    ADD CONSTRAINT uq_idea_translation_section
    UNIQUE (idea_id, language, section_name);
