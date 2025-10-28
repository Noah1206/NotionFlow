-- Fix platform_coverage foreign key constraint issues
-- This migration makes the trigger function more robust to handle missing users

-- Update the trigger function to create user if not exists
CREATE OR REPLACE FUNCTION update_platform_coverage()
RETURNS TRIGGER AS $$
BEGIN
  -- Update platform coverage when sync events are recorded
  IF NEW.event_type IN ('sync_completed', 'sync_failed') THEN

    -- First, ensure the user exists to prevent foreign key violations
    INSERT INTO users (id, email, created_at, updated_at)
    VALUES (
      NEW.user_id,
      CONCAT(LEFT(NEW.user_id, 8), '@notionflow.app'),
      NOW(),
      NOW()
    )
    ON CONFLICT (id) DO NOTHING;  -- If user already exists, do nothing

    -- Now safely insert/update platform coverage
    INSERT INTO platform_coverage (
      user_id,
      platform,
      is_connected,
      first_connected_at,
      last_active_at,
      total_synced_items,
      total_failed_items
    )
    VALUES (
      NEW.user_id,
      NEW.platform,
      true,
      NOW(),
      NOW(),
      CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
      CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END
    )
    ON CONFLICT (user_id, platform)
    DO UPDATE SET
      last_active_at = NOW(),
      total_synced_items = platform_coverage.total_synced_items +
        CASE WHEN NEW.status = 'success' THEN 1 ELSE 0 END,
      total_failed_items = platform_coverage.total_failed_items +
        CASE WHEN NEW.status = 'failed' THEN 1 ELSE 0 END,
      sync_success_rate = CASE
        WHEN (platform_coverage.total_synced_items + platform_coverage.total_failed_items) > 0
        THEN ROUND(
          (platform_coverage.total_synced_items::numeric /
          (platform_coverage.total_synced_items + platform_coverage.total_failed_items)) * 100,
          2
        )
        ELSE 0.00
      END;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Comment explaining the fix
COMMENT ON FUNCTION update_platform_coverage() IS 'Updated trigger function that safely creates users before inserting into platform_coverage to prevent foreign key constraint violations';