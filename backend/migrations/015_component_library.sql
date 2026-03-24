-- 015_component_library.sql: Component library table with seed data

CREATE TABLE IF NOT EXISTS component_library (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug                  TEXT NOT NULL UNIQUE,
  name                  TEXT NOT NULL,
  domain                TEXT NOT NULL DEFAULT '',
  category              TEXT NOT NULL DEFAULT '',
  logo_base64           TEXT,
  is_native_connector   BOOLEAN NOT NULL DEFAULT false,
  display_order         INTEGER NOT NULL DEFAULT 0,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed data: ~28 systems across 10 categories
-- Uses ON CONFLICT (slug) DO NOTHING for idempotent re-runs
INSERT INTO component_library (slug, name, domain, category, is_native_connector, display_order) VALUES
-- CRM
('salesforce', 'Salesforce', 'salesforce.com', 'CRM', true, 10),
('hubspot', 'HubSpot', 'hubspot.com', 'CRM', true, 11),
-- Billing/Payments
('stripe', 'Stripe', 'stripe.com', 'Billing/Payments', true, 20),
('chargebee', 'Chargebee', 'chargebee.com', 'Billing/Payments', true, 21),
('paddle', 'Paddle', 'paddle.com', 'Billing/Payments', true, 22),
('zuora', 'Zuora', 'zuora.com', 'Billing/Payments', false, 23),
('recurly', 'Recurly', 'recurly.com', 'Billing/Payments', false, 24),
-- Finance/ERP
('netsuite', 'NetSuite', 'netsuite.com', 'Finance/ERP', true, 30),
('quickbooks', 'QuickBooks', 'quickbooks.intuit.com', 'Finance/ERP', true, 31),
('xero', 'Xero', 'xero.com', 'Finance/ERP', true, 32),
('sap', 'SAP', 'sap.com', 'Finance/ERP', false, 33),
-- Cloud Marketplace
('aws-marketplace', 'AWS Marketplace', 'aws.amazon.com', 'Cloud Marketplace', true, 40),
('azure-marketplace', 'Azure Marketplace', 'azure.microsoft.com', 'Cloud Marketplace', true, 41),
-- Analytics
('snowflake', 'Snowflake', 'snowflake.com', 'Analytics', false, 50),
('bigquery', 'BigQuery', 'cloud.google.com', 'Analytics', false, 51),
('redshift', 'Redshift', 'aws.amazon.com', 'Analytics', false, 52),
('looker', 'Looker', 'looker.com', 'Analytics', false, 53),
-- Data Infrastructure
('segment', 'Segment', 'segment.com', 'Data Infrastructure', false, 60),
('fivetran', 'Fivetran', 'fivetran.com', 'Data Infrastructure', false, 61),
-- Cloud Providers
('aws', 'AWS', 'aws.amazon.com', 'Cloud Providers', false, 70),
('azure', 'Azure', 'azure.microsoft.com', 'Cloud Providers', false, 71),
('gcp', 'GCP', 'cloud.google.com', 'Cloud Providers', false, 72),
-- Monitoring
('datadog', 'Datadog', 'datadoghq.com', 'Monitoring', false, 80),
('grafana', 'Grafana', 'grafana.com', 'Monitoring', false, 81),
-- Messaging
('slack', 'Slack', 'slack.com', 'Messaging', false, 90),
('twilio', 'Twilio', 'twilio.com', 'Messaging', false, 91),
('sendgrid', 'SendGrid', 'sendgrid.com', 'Messaging', false, 92),
-- Developer Tools
('github', 'GitHub', 'github.com', 'Developer Tools', false, 100),
('jira', 'Jira', 'atlassian.com', 'Developer Tools', false, 101)
ON CONFLICT (slug) DO NOTHING;
