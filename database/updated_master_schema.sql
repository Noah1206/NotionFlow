-- ============================================
-- 🚀 NodeFlow Complete Database Schema
-- Updated with actual production schema structure
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 📊 CORE TABLES
-- ============================================

-- Users table (main user accounts)
CREATE TABLE public.users (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  email character varying NOT NULL UNIQUE,
  name character varying DEFAULT 'User'::character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  is_active boolean DEFAULT true,
  subscription_plan character varying DEFAULT 'free'::character varying CHECK (subscription_plan::text = ANY (ARRAY['free'::character varying, 'pro'::character varying, 'enterprise'::character varying]::text[])),
  subscription_expires_at timestamp with time zone,
  last_login_at timestamp with time zone,
  email_verified boolean DEFAULT false,
  avatar_url text,
  timezone character varying DEFAULT 'UTC'::character varying,
  CONSTRAINT users_pkey PRIMARY KEY (id)
);

-- User profiles for additional user information
CREATE TABLE public.user_profiles (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid,
  username character varying NOT NULL UNIQUE CHECK (username::text ~ '^[a-zA-Z0-9_]{3,30}$'::text),
  display_name character varying,
  bio text,
  website_url text,
  is_public boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  avatar_url text,
  email character varying,
  encrypted_email text,
  birthdate date DEFAULT '1990-01-01'::date,
  CONSTRAINT user_profiles_pkey PRIMARY KEY (id)
);

-- ============================================
-- 📅 CALENDAR SYSTEM
-- ============================================

-- Main calendars table (USES owner_id!)
CREATE TABLE public.calendars (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  owner_id text NOT NULL,  -- ⚠️ IMPORTANT: Uses owner_id, not user_id!
  type character varying NOT NULL CHECK (type::text = ANY (ARRAY['personal'::character varying, 'shared'::character varying]::text[])),
  name character varying DEFAULT 'My Calendar'::character varying,
  description text,
  color character varying DEFAULT '#3B82F6'::character varying,
  share_link text,
  is_active boolean DEFAULT true,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  public_access boolean DEFAULT false,
  allow_editing boolean DEFAULT false,
  media_filename text,
  media_file_path text,
  media_file_type text,
  CONSTRAINT calendars_pkey PRIMARY KEY (id)
);

-- Calendar events
CREATE TABLE public.calendar_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  title character varying NOT NULL,
  description text,
  start_datetime timestamp with time zone NOT NULL,
  end_datetime timestamp with time zone NOT NULL,
  is_all_day boolean DEFAULT false,
  category character varying,
  priority integer DEFAULT 0 CHECK (priority >= 0 AND priority <= 2),
  status character varying DEFAULT 'confirmed'::character varying,
  source_platform character varying NOT NULL CHECK (source_platform::text = ANY (ARRAY['google'::character varying, 'notion'::character varying, 'apple'::character varying, 'outlook'::character varying, 'manual'::character varying]::text[])),
  external_id character varying,
  external_url text,
  last_synced_at timestamp with time zone DEFAULT now(),
  sync_status character varying DEFAULT 'synced'::character varying CHECK (sync_status::text = ANY (ARRAY['synced'::character varying, 'pending'::character varying, 'error'::character varying, 'conflict'::character varying]::text[])),
  sync_hash character varying,
  location text,
  attendees jsonb,
  recurrence_rule text,
  parent_event_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  source_calendar_id text,
  source_calendar_name text,
  calendar_id uuid,
  CONSTRAINT calendar_events_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_events_parent_event_id_fkey FOREIGN KEY (parent_event_id) REFERENCES public.calendar_events(id),
  CONSTRAINT calendar_events_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id),
  CONSTRAINT calendar_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);

-- Calendar sharing system
CREATE TABLE public.calendar_shares (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  calendar_id uuid,
  user_id text NOT NULL,
  access_level character varying DEFAULT 'view'::character varying CHECK (access_level::text = ANY (ARRAY['view'::character varying, 'edit'::character varying, 'admin'::character varying]::text[])),
  shared_by text,
  shared_at timestamp with time zone DEFAULT now(),
  is_active boolean DEFAULT true,
  CONSTRAINT calendar_shares_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_shares_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id)
);

-- Calendar members (for team calendars)
CREATE TABLE public.calendar_members (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  calendar_id uuid,
  user_id text NOT NULL,
  role character varying NOT NULL CHECK (role::text = ANY (ARRAY['owner'::character varying, 'admin'::character varying, 'member'::character varying, 'viewer'::character varying]::text[])),
  permissions json DEFAULT '{"read": true, "write": false, "delete": false}'::json,
  joined_at timestamp with time zone DEFAULT now(),
  invited_by text,
  CONSTRAINT calendar_members_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_members_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id)
);

-- Calendar share tokens (for public sharing)
CREATE TABLE public.calendar_share_tokens (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  calendar_id uuid,
  token character varying NOT NULL UNIQUE,
  permissions json DEFAULT '{"read": true}'::json,
  expires_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  last_accessed_at timestamp with time zone,
  CONSTRAINT calendar_share_tokens_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_share_tokens_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id)
);

-- Calendar tags system
CREATE TABLE public.calendar_tags (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  name character varying NOT NULL,
  color character varying DEFAULT '#FF4539'::character varying,
  description text,
  is_system boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT calendar_tags_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_tags_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Event-tag relationships
CREATE TABLE public.event_tags (
  event_id uuid NOT NULL,
  tag_id uuid NOT NULL,
  CONSTRAINT event_tags_pkey PRIMARY KEY (event_id, tag_id),
  CONSTRAINT event_tags_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.calendar_events(id),
  CONSTRAINT event_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.calendar_tags(id)
);

-- Event attendees
CREATE TABLE public.event_attendees (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  event_id uuid,
  user_id text,
  email character varying,
  name character varying,
  status character varying DEFAULT 'pending'::character varying CHECK (status::text = ANY (ARRAY['pending'::character varying, 'accepted'::character varying, 'declined'::character varying, 'tentative'::character varying]::text[])),
  is_organizer boolean DEFAULT false,
  added_at timestamp with time zone DEFAULT now(),
  CONSTRAINT event_attendees_pkey PRIMARY KEY (id),
  CONSTRAINT event_attendees_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.calendar_events(id)
);

-- ============================================
-- 🔄 SYNCHRONIZATION SYSTEM
-- ============================================

-- Calendar sync configurations
CREATE TABLE public.calendar_sync_configs (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid,
  platform character varying NOT NULL CHECK (platform::text = ANY (ARRAY['notion'::character varying, 'google'::character varying, 'apple'::character varying, 'outlook'::character varying, 'slack'::character varying]::text[])),
  credentials jsonb NOT NULL,
  is_enabled boolean DEFAULT true,
  sync_direction character varying DEFAULT 'bidirectional'::character varying CHECK (sync_direction::text = ANY (ARRAY['import_only'::character varying, 'export_only'::character varying, 'bidirectional'::character varying]::text[])),
  sync_frequency_minutes integer DEFAULT 15 CHECK (sync_frequency_minutes >= 5),
  last_sync_at timestamp with time zone,
  next_sync_at timestamp with time zone,
  consecutive_failures integer DEFAULT 0,
  last_error_message text,
  sync_errors jsonb DEFAULT '[]'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  calendar_id uuid,
  CONSTRAINT calendar_sync_configs_pkey PRIMARY KEY (id),
  CONSTRAINT calendar_sync_configs_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id)
);

-- Calendar sync status tracking
CREATE TABLE public.calendar_sync (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  platform text NOT NULL,
  calendar_id uuid NOT NULL,
  sync_status text DEFAULT 'active'::text,
  synced_at timestamp with time zone DEFAULT now(),
  last_sync_at timestamp with time zone,
  sync_frequency_minutes integer DEFAULT 15,
  consecutive_failures integer DEFAULT 0,
  error_message text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT calendar_sync_pkey PRIMARY KEY (id)
);

-- Sync status table
CREATE TABLE public.sync_status (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  platform text NOT NULL CHECK (platform = ANY (ARRAY['notion'::text, 'google_calendar'::text, 'apple_calendar'::text, 'slack'::text, 'outlook'::text])),
  is_synced boolean DEFAULT false,
  is_connected boolean DEFAULT false,
  last_sync_at timestamp with time zone,
  next_sync_at timestamp with time zone,
  sync_frequency integer DEFAULT 15,
  is_active boolean DEFAULT true,
  error_message text,
  items_synced integer DEFAULT 0,
  items_failed integer DEFAULT 0,
  sync_duration_ms integer,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sync_status_pkey PRIMARY KEY (id),
  CONSTRAINT sync_status_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Sync events logging
CREATE TABLE public.sync_events (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  event_type character varying NOT NULL CHECK (event_type::text = ANY (ARRAY['sync_started'::character varying, 'sync_completed'::character varying, 'sync_failed'::character varying, 'item_created'::character varying, 'item_updated'::character varying, 'item_deleted'::character varying, 'platform_connected'::character varying, 'platform_disconnected'::character varying]::text[])),
  platform character varying NOT NULL CHECK (platform::text = ANY (ARRAY['notion'::character varying, 'google'::character varying, 'slack'::character varying, 'outlook'::character varying, 'todoist'::character varying, 'apple'::character varying]::text[])),
  source_platform character varying,
  target_platform character varying,
  item_type character varying CHECK (item_type::text = ANY (ARRAY['task'::character varying, 'event'::character varying, 'note'::character varying, 'meeting'::character varying, 'calendar'::character varying, NULL::character varying]::text[])),
  item_id text,
  item_title text,
  status character varying CHECK (status::text = ANY (ARRAY['success'::character varying, 'failed'::character varying, 'skipped'::character varying, 'pending'::character varying]::text[])),
  error_message text,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  sync_job_id uuid,
  CONSTRAINT sync_events_pkey PRIMARY KEY (id)
);

-- Sync logs
CREATE TABLE public.sync_logs (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid,
  config_id uuid,
  platform character varying NOT NULL,
  sync_type character varying NOT NULL CHECK (sync_type::text = ANY (ARRAY['manual'::character varying, 'scheduled'::character varying, 'webhook'::character varying]::text[])),
  status character varying NOT NULL CHECK (status::text = ANY (ARRAY['success'::character varying, 'error'::character varying, 'partial'::character varying]::text[])),
  events_imported integer DEFAULT 0,
  events_exported integer DEFAULT 0,
  events_updated integer DEFAULT 0,
  events_deleted integer DEFAULT 0,
  error_message text,
  error_details jsonb,
  duration_ms integer,
  started_at timestamp with time zone NOT NULL,
  completed_at timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sync_logs_pkey PRIMARY KEY (id),
  CONSTRAINT sync_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id),
  CONSTRAINT sync_logs_config_id_fkey FOREIGN KEY (config_id) REFERENCES public.calendar_sync_configs(id)
);

-- Sync analytics
CREATE TABLE public.sync_analytics (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  period_type character varying NOT NULL CHECK (period_type::text = ANY (ARRAY['hourly'::character varying, 'daily'::character varying, 'weekly'::character varying, 'monthly'::character varying]::text[])),
  period_start timestamp with time zone NOT NULL,
  period_end timestamp with time zone NOT NULL,
  total_syncs integer DEFAULT 0,
  successful_syncs integer DEFAULT 0,
  failed_syncs integer DEFAULT 0,
  items_created integer DEFAULT 0,
  items_updated integer DEFAULT 0,
  items_deleted integer DEFAULT 0,
  avg_sync_time_ms integer DEFAULT 0,
  platform_breakdown jsonb DEFAULT '{}'::jsonb,
  error_breakdown jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT sync_analytics_pkey PRIMARY KEY (id),
  CONSTRAINT sync_analytics_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- ============================================
-- 🔐 AUTHENTICATION & OAUTH
-- ============================================

-- OAuth tokens storage
CREATE TABLE public.oauth_tokens (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  platform character varying NOT NULL,
  access_token text NOT NULL,
  refresh_token text,
  token_type character varying DEFAULT 'Bearer'::character varying,
  expires_at timestamp with time zone,
  scope text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT oauth_tokens_pkey PRIMARY KEY (id)
);

-- OAuth states for security
CREATE TABLE public.oauth_states (
  id integer NOT NULL DEFAULT nextval('oauth_states_id_seq'::regclass),
  user_id character varying NOT NULL,
  provider character varying NOT NULL,
  state character varying NOT NULL UNIQUE,
  code_verifier character varying,
  created_at timestamp without time zone DEFAULT now(),
  expires_at timestamp without time zone NOT NULL,
  CONSTRAINT oauth_states_pkey PRIMARY KEY (id)
);

-- Platform connections tracking
CREATE TABLE public.platform_connections (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid,
  platform character varying NOT NULL,
  is_connected boolean DEFAULT false,
  connection_status character varying DEFAULT 'disconnected'::character varying,
  last_sync_at timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  access_token text,
  refresh_token text,
  token_expires_at timestamp with time zone,
  connection_method character varying DEFAULT 'oauth'::character varying,
  CONSTRAINT platform_connections_pkey PRIMARY KEY (id)
);

-- Platform coverage analytics
CREATE TABLE public.platform_coverage (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  platform character varying NOT NULL,
  is_connected boolean DEFAULT false,
  first_connected_at timestamp with time zone,
  last_active_at timestamp with time zone,
  total_synced_items integer DEFAULT 0,
  total_failed_items integer DEFAULT 0,
  sync_success_rate numeric DEFAULT 0.00,
  avg_sync_duration_ms integer DEFAULT 0,
  feature_coverage jsonb DEFAULT '{"webhooks": false, "real_time": false, "sync_notes": false, "sync_tasks": false, "sync_events": false, "bidirectional": false}'::jsonb,
  platform_config jsonb DEFAULT '{}'::jsonb,
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT platform_coverage_pkey PRIMARY KEY (id),
  CONSTRAINT platform_coverage_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- ============================================
-- 🔄 EVENT VALIDATION & SYNC QUEUE
-- ============================================

-- Event validation history
CREATE TABLE public.event_validation_history (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  calendar_id uuid NOT NULL,
  source_event_id uuid NOT NULL,
  target_platform character varying NOT NULL,
  target_event_id character varying,
  tier1_db_check boolean NOT NULL,
  tier2_trash_check boolean NOT NULL,
  tier3_duplicate_check boolean NOT NULL,
  content_hash character varying NOT NULL,
  normalized_title character varying NOT NULL,
  event_date date NOT NULL,
  event_start_time time without time zone,
  validation_status character varying NOT NULL DEFAULT 'pending'::character varying CHECK (validation_status::text = ANY (ARRAY['pending'::character varying, 'approved'::character varying, 'rejected'::character varying, 'synced'::character varying]::text[])),
  rejection_reason text,
  case_classification character varying,
  sync_attempted_at timestamp with time zone,
  sync_completed_at timestamp with time zone,
  sync_status character varying DEFAULT 'pending'::character varying CHECK (sync_status::text = ANY (ARRAY['pending'::character varying, 'success'::character varying, 'failed'::character varying]::text[])),
  sync_error_message text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT event_validation_history_pkey PRIMARY KEY (id),
  CONSTRAINT event_validation_history_calendar_id_fkey FOREIGN KEY (calendar_id) REFERENCES public.calendars(id),
  CONSTRAINT event_validation_history_source_event_id_fkey FOREIGN KEY (source_event_id) REFERENCES public.calendar_events(id)
);

-- Event sync queue
CREATE TABLE public.event_sync_queue (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  batch_id uuid NOT NULL DEFAULT uuid_generate_v4(),
  priority integer DEFAULT 5,
  source_event_id uuid NOT NULL,
  target_platform character varying NOT NULL,
  sync_action character varying NOT NULL CHECK (sync_action::text = ANY (ARRAY['create'::character varying, 'update'::character varying, 'delete'::character varying]::text[])),
  status character varying DEFAULT 'queued'::character varying CHECK (status::text = ANY (ARRAY['queued'::character varying, 'processing'::character varying, 'completed'::character varying, 'failed'::character varying]::text[])),
  retry_count integer DEFAULT 0,
  max_retries integer DEFAULT 3,
  scheduled_at timestamp with time zone DEFAULT now(),
  started_at timestamp with time zone,
  completed_at timestamp with time zone,
  error_message text,
  validation_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT event_sync_queue_pkey PRIMARY KEY (id),
  CONSTRAINT event_sync_queue_source_event_id_fkey FOREIGN KEY (source_event_id) REFERENCES public.calendar_events(id),
  CONSTRAINT event_sync_queue_validation_id_fkey FOREIGN KEY (validation_id) REFERENCES public.event_validation_history(id)
);

-- Event sync mapping
CREATE TABLE public.event_sync_mapping (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  notion_event_id character varying NOT NULL,
  notion_calendar_id character varying,
  platform character varying NOT NULL,
  external_event_id character varying NOT NULL,
  external_calendar_id character varying,
  sync_status character varying DEFAULT 'synced'::character varying,
  last_sync_direction character varying,
  created_at timestamp with time zone DEFAULT now(),
  synced_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  sync_metadata jsonb,
  error_message text,
  CONSTRAINT event_sync_mapping_pkey PRIMARY KEY (id),
  CONSTRAINT event_sync_mapping_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- Event content fingerprints (for duplicate detection)
CREATE TABLE public.event_content_fingerprints (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  platform character varying NOT NULL,
  content_hash character varying NOT NULL,
  normalized_title character varying NOT NULL,
  event_date date NOT NULL,
  event_start_time time without time zone,
  source_event_id uuid,
  external_event_id character varying,
  is_active boolean DEFAULT true,
  last_verified_at timestamp with time zone DEFAULT now(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT event_content_fingerprints_pkey PRIMARY KEY (id)
);

-- ============================================
-- 👥 SOCIAL FEATURES
-- ============================================

-- Friendships system
CREATE TABLE public.friendships (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL,
  friend_id uuid NOT NULL,
  status character varying NOT NULL DEFAULT 'pending'::character varying CHECK (status::text = ANY (ARRAY['pending'::character varying, 'accepted'::character varying, 'blocked'::character varying, 'declined'::character varying]::text[])),
  created_at timestamp with time zone DEFAULT now(),
  accepted_at timestamp with time zone,
  blocked_at timestamp with time zone,
  notes text,
  CONSTRAINT friendships_pkey PRIMARY KEY (id),
  CONSTRAINT friendships_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id),
  CONSTRAINT friendships_friend_id_fkey FOREIGN KEY (friend_id) REFERENCES auth.users(id)
);

-- ============================================
-- 💳 BILLING & SUBSCRIPTIONS
-- ============================================

-- User subscriptions
CREATE TABLE public.user_subscriptions (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL UNIQUE,
  plan_type character varying NOT NULL DEFAULT 'free'::character varying CHECK (plan_type::text = ANY (ARRAY['free'::character varying, 'premium'::character varying, 'pro'::character varying, 'enterprise'::character varying]::text[])),
  billing_cycle character varying DEFAULT 'monthly'::character varying CHECK (billing_cycle::text = ANY (ARRAY['monthly'::character varying, 'yearly'::character varying]::text[])),
  status character varying DEFAULT 'active'::character varying CHECK (status::text = ANY (ARRAY['active'::character varying, 'cancelled'::character varying, 'past_due'::character varying, 'unpaid'::character varying]::text[])),
  current_period_start timestamp with time zone DEFAULT now(),
  current_period_end timestamp with time zone,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_subscriptions_pkey PRIMARY KEY (id),
  CONSTRAINT user_subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- ============================================
-- 📊 ANALYTICS & TRACKING
-- ============================================

-- User activity tracking
CREATE TABLE public.user_activity (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  activity_type character varying NOT NULL CHECK (activity_type::text = ANY (ARRAY['login'::character varying, 'logout'::character varying, 'sync_triggered'::character varying, 'sync_scheduled'::character varying, 'settings_changed'::character varying, 'platform_connected'::character varying, 'platform_disconnected'::character varying, 'api_key_added'::character varying, 'api_key_removed'::character varying, 'subscription_changed'::character varying]::text[])),
  platform character varying,
  activity_details jsonb DEFAULT '{}'::jsonb,
  ip_address inet,
  user_agent text,
  session_id text,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_activity_pkey PRIMARY KEY (id),
  CONSTRAINT user_activity_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- User visits tracking
CREATE TABLE public.user_visits (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  visit_type character varying NOT NULL DEFAULT 'calendar_page'::character varying,
  visit_count integer DEFAULT 1,
  first_visit_at timestamp with time zone DEFAULT now(),
  last_visit_at timestamp with time zone DEFAULT now(),
  popup_shown boolean DEFAULT false,
  popup_shown_at timestamp with time zone,
  popup_dismissed boolean DEFAULT false,
  popup_dismissed_at timestamp with time zone,
  calendar_created boolean DEFAULT false,
  calendar_created_at timestamp with time zone,
  user_agent text,
  ip_address inet,
  session_data jsonb DEFAULT '{}'::jsonb,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT user_visits_pkey PRIMARY KEY (id)
);

-- ============================================
-- ⚙️ SETTINGS & PREFERENCES
-- ============================================

-- Notification preferences
CREATE TABLE public.notification_preferences (
  id uuid NOT NULL DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL UNIQUE,
  email_notifications boolean DEFAULT true,
  push_notifications boolean DEFAULT true,
  ai_processing_enabled boolean DEFAULT false,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  CONSTRAINT notification_preferences_pkey PRIMARY KEY (id),
  CONSTRAINT notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id)
);

-- ============================================
-- 📈 INDEXES (Performance Optimization)
-- ============================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- User profiles indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_username ON user_profiles(username);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- ⚠️ CRITICAL: Calendars indexes (uses owner_id!)
CREATE INDEX IF NOT EXISTS idx_calendars_owner_id ON calendars(owner_id);
CREATE INDEX IF NOT EXISTS idx_calendars_type ON calendars(type);
CREATE INDEX IF NOT EXISTS idx_calendars_is_active ON calendars(is_active);

-- Calendar events indexes
CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_calendar_id ON calendar_events(calendar_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_datetime ON calendar_events(start_datetime);
CREATE INDEX IF NOT EXISTS idx_calendar_events_source_platform ON calendar_events(source_platform);

-- Sync related indexes
CREATE INDEX IF NOT EXISTS idx_calendar_sync_user_id ON calendar_sync(user_id);
CREATE INDEX IF NOT EXISTS idx_calendar_sync_platform ON calendar_sync(platform);
CREATE INDEX IF NOT EXISTS idx_sync_status_user_id ON sync_status(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_status_platform ON sync_status(platform);

-- OAuth and auth indexes
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_platform ON oauth_tokens(platform);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_user_visits_user_id ON user_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_events_user_id ON sync_events(user_id);

-- ============================================
-- 🎉 SCHEMA COMPLETE
-- ============================================

-- Table count: 26 tables
-- Key insight: calendars table uses owner_id (TEXT), not user_id!