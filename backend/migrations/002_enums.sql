-- 002_enums.sql: All enum types and set_updated_at() trigger function

-- Entity types for m3ter configuration objects
DO $$ BEGIN
  CREATE TYPE entity_type AS ENUM (
    'product', 'meter', 'aggregation', 'compound_aggregation',
    'plan_template', 'plan', 'pricing', 'account', 'account_plan', 'measurement'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Status of AI-generated objects
DO $$ BEGIN
  CREATE TYPE object_status AS ENUM (
    'draft', 'approved', 'rejected', 'pushed', 'push_failed'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- LangGraph workflow types
DO $$ BEGIN
  CREATE TYPE workflow_type AS ENUM (
    'product_meter_aggregation', 'plan_pricing', 'account_setup', 'usage_submission'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Workflow execution status
DO $$ BEGIN
  CREATE TYPE workflow_status AS ENUM (
    'pending', 'running', 'interrupted', 'completed', 'failed'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Use case lifecycle status
DO $$ BEGIN
  CREATE TYPE use_case_status AS ENUM (
    'draft', 'in_progress', 'completed'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Billing frequency options
DO $$ BEGIN
  CREATE TYPE billing_frequency AS ENUM (
    'monthly', 'quarterly', 'annually'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- m3ter org connection status
DO $$ BEGIN
  CREATE TYPE connection_status AS ENUM (
    'active', 'inactive', 'error'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Document processing status
DO $$ BEGIN
  CREATE TYPE document_status AS ENUM (
    'pending', 'processing', 'ready', 'failed'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Embedding source type
DO $$ BEGIN
  CREATE TYPE embedding_source AS ENUM (
    'm3ter_docs', 'user_document'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Chat message roles
DO $$ BEGIN
  CREATE TYPE message_role AS ENUM (
    'user', 'assistant', 'system'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Trigger function: auto-update updated_at column
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
