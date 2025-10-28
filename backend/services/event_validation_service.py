"""
🛡️ Event Validation Service
3-tier validation system for preventing duplicate calendar events during sync
"""

import os
import json
import hashlib
from datetime import datetime, timezone, date, time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from supabase import create_client

# Validation result enums
class ValidationResult(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"

class CaseClassification(Enum):
    NEW_EVENT = "new_event"
    CONTENT_CHANGE = "content_change"
    DATE_CHANGE = "date_change"
    DELETION = "deletion"
    DUPLICATE_CONTENT = "duplicate_content"
    TRASHED_EVENT = "trashed_event"
    MISSING_EVENT = "missing_event"

@dataclass
class ValidationTier:
    """Represents a single validation tier result"""
    tier_number: int
    passed: bool
    description: str
    details: Optional[Dict] = None

@dataclass
class ValidationReport:
    """Complete validation report for an event"""
    event_id: str
    target_platform: str
    tier1: ValidationTier  # DB existence check
    tier2: ValidationTier  # Trash check
    tier3: ValidationTier  # Duplicate content check
    overall_result: ValidationResult
    case_classification: CaseClassification
    content_hash: str
    rejection_reason: Optional[str] = None
    validation_id: Optional[str] = None

class EventValidationService:
    """3-tier event validation service for sync operations"""

    def __init__(self):
        """Initialize the validation service"""
        # Supabase configuration
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found")

        self.supabase = create_client(self.supabase_url, self.supabase_key)
        print("✅ [VALIDATION] Service initialized")

    def generate_content_hash(self, title: str, event_date: date, event_time: Optional[time] = None) -> str:
        """Generate SHA-256 hash for content fingerprinting"""
        try:
            # Normalize title: lowercase, strip whitespace
            normalized_title = title.lower().strip() if title else ""

            # Create content string
            content_parts = [
                normalized_title,
                str(event_date) if event_date else "",
                str(event_time) if event_time else ""
            ]
            content_string = "|".join(content_parts)

            # Generate SHA-256 hash
            content_hash = hashlib.sha256(content_string.encode('utf-8')).hexdigest()

            print(f"🔐 [VALIDATION] Generated hash for '{normalized_title}' on {event_date}: {content_hash[:12]}...")
            return content_hash

        except Exception as e:
            print(f"❌ [VALIDATION] Error generating content hash: {e}")
            return ""

    def tier1_db_existence_check(self, user_id: str, event_id: str) -> ValidationTier:
        """Tier 1: Check if event exists in database and is not cancelled"""
        try:
            print(f"🔍 [VALIDATION] Tier 1: Checking DB existence for event {event_id}")

            # Query calendar_events table
            result = self.supabase.table('calendar_events').select(
                'id, title, status, calendar_id, start_datetime, end_datetime, start_date, end_date, is_all_day'
            ).eq('user_id', user_id).eq('id', event_id).execute()

            if not result.data:
                print(f"❌ [VALIDATION] Tier 1 FAILED: Event {event_id} not found")
                return ValidationTier(
                    tier_number=1,
                    passed=False,
                    description="Event not found in database",
                    details={'reason': 'event_not_found'}
                )

            event = result.data[0]

            # Check if event is cancelled
            if event.get('status') == 'cancelled':
                print(f"❌ [VALIDATION] Tier 1 FAILED: Event {event_id} is cancelled")
                return ValidationTier(
                    tier_number=1,
                    passed=False,
                    description="Event is cancelled",
                    details={'reason': 'event_cancelled', 'status': event.get('status')}
                )

            print(f"✅ [VALIDATION] Tier 1 PASSED: Event {event_id} exists and is active")
            return ValidationTier(
                tier_number=1,
                passed=True,
                description="Event exists in database and is active",
                details={'event_data': event}
            )

        except Exception as e:
            print(f"❌ [VALIDATION] Tier 1 ERROR: {e}")
            return ValidationTier(
                tier_number=1,
                passed=False,
                description=f"Database check failed: {str(e)}",
                details={'error': str(e)}
            )

    def tier2_trash_check(self, event_id: str, calendar_id: str, trashed_events: List[Dict]) -> ValidationTier:
        """Tier 2: Check if event is in localStorage trash"""
        try:
            print(f"🗑️ [VALIDATION] Tier 2: Checking trash status for event {event_id}")

            # Check if event is in the provided trashed events list
            for trashed_event in trashed_events:
                if (trashed_event.get('id') == event_id or
                    trashed_event.get('event_id') == event_id) and \
                   trashed_event.get('calendarId') == calendar_id:

                    print(f"❌ [VALIDATION] Tier 2 FAILED: Event {event_id} is in trash")
                    return ValidationTier(
                        tier_number=2,
                        passed=False,
                        description="Event is in trash",
                        details={
                            'reason': 'event_in_trash',
                            'deleted_at': trashed_event.get('deletedAt'),
                            'trash_entry': trashed_event
                        }
                    )

            print(f"✅ [VALIDATION] Tier 2 PASSED: Event {event_id} not in trash")
            return ValidationTier(
                tier_number=2,
                passed=True,
                description="Event is not in trash",
                details={'trash_count_checked': len(trashed_events)}
            )

        except Exception as e:
            print(f"❌ [VALIDATION] Tier 2 ERROR: {e}")
            return ValidationTier(
                tier_number=2,
                passed=False,
                description=f"Trash check failed: {str(e)}",
                details={'error': str(e)}
            )

    def tier3_duplicate_content_check(self, user_id: str, target_platform: str,
                                      content_hash: str, event_data: Dict) -> ValidationTier:
        """Tier 3: Check for duplicate content on target platform"""
        try:
            print(f"🔍 [VALIDATION] Tier 3: Checking duplicate content for platform {target_platform}")
            print(f"🔐 [VALIDATION] Content hash: {content_hash[:12]}...")

            # Query event_content_fingerprints table
            result = self.supabase.table('event_content_fingerprints').select(
                'id, content_hash, normalized_title, event_date, external_event_id, source_event_id'
            ).eq('user_id', user_id).eq('platform', target_platform).eq(
                'content_hash', content_hash
            ).eq('is_active', True).execute()

            if result.data:
                existing_fingerprint = result.data[0]
                print(f"❌ [VALIDATION] Tier 3 FAILED: Duplicate content found")
                print(f"📋 [VALIDATION] Existing: {existing_fingerprint.get('normalized_title')} on {existing_fingerprint.get('event_date')}")

                return ValidationTier(
                    tier_number=3,
                    passed=False,
                    description="Duplicate content detected on target platform",
                    details={
                        'reason': 'duplicate_content',
                        'existing_fingerprint': existing_fingerprint,
                        'content_hash': content_hash
                    }
                )

            print(f"✅ [VALIDATION] Tier 3 PASSED: No duplicate content found")
            return ValidationTier(
                tier_number=3,
                passed=True,
                description="No duplicate content detected",
                details={'content_hash': content_hash, 'platform': target_platform}
            )

        except Exception as e:
            print(f"❌ [VALIDATION] Tier 3 ERROR: {e}")
            return ValidationTier(
                tier_number=3,
                passed=False,
                description=f"Duplicate check failed: {str(e)}",
                details={'error': str(e)}
            )

    def classify_event_case(self, event_data: Dict, tier_results: Dict) -> CaseClassification:
        """Classify the type of event change/action"""
        try:
            # Analyze tier results to determine case classification
            tier1_passed = tier_results['tier1'].passed
            tier2_passed = tier_results['tier2'].passed
            tier3_passed = tier_results['tier3'].passed

            if not tier1_passed:
                tier1_reason = tier_results['tier1'].details.get('reason', '')
                if tier1_reason == 'event_not_found':
                    return CaseClassification.MISSING_EVENT
                elif tier1_reason == 'event_cancelled':
                    return CaseClassification.DELETION
                else:
                    return CaseClassification.MISSING_EVENT

            if not tier2_passed:
                return CaseClassification.TRASHED_EVENT

            if not tier3_passed:
                # Check if it's the same event or truly duplicate
                existing_fingerprint = tier_results['tier3'].details.get('existing_fingerprint', {})
                current_event_id = event_data.get('id')
                existing_source_id = existing_fingerprint.get('source_event_id')

                if str(current_event_id) == str(existing_source_id):
                    # Same event, might be content or date change
                    # This would require more sophisticated analysis
                    return CaseClassification.CONTENT_CHANGE
                else:
                    return CaseClassification.DUPLICATE_CONTENT

            # All tiers passed - new event
            return CaseClassification.NEW_EVENT

        except Exception as e:
            print(f"⚠️ [VALIDATION] Error classifying case: {e}")
            return CaseClassification.NEW_EVENT

    def validate_event_for_sync(self, user_id: str, event_id: str, target_platform: str,
                                trashed_events: List[Dict] = None) -> ValidationReport:
        """Perform complete 3-tier validation for an event"""
        try:
            print(f"🚀 [VALIDATION] Starting 3-tier validation for event {event_id} → {target_platform}")

            if trashed_events is None:
                trashed_events = []

            # Tier 1: Database existence check
            tier1 = self.tier1_db_existence_check(user_id, event_id)

            if not tier1.passed:
                # Early exit if event doesn't exist or is cancelled
                case_classification = self.classify_event_case({}, {'tier1': tier1, 'tier2': None, 'tier3': None})

                return ValidationReport(
                    event_id=event_id,
                    target_platform=target_platform,
                    tier1=tier1,
                    tier2=ValidationTier(2, False, "Skipped due to Tier 1 failure"),
                    tier3=ValidationTier(3, False, "Skipped due to Tier 1 failure"),
                    overall_result=ValidationResult.REJECTED,
                    case_classification=case_classification,
                    content_hash="",
                    rejection_reason=tier1.description
                )

            # Get event data for further processing
            event_data = tier1.details['event_data']
            calendar_id = event_data.get('calendar_id')

            # Tier 2: Trash check
            tier2 = self.tier2_trash_check(event_id, calendar_id, trashed_events)

            if not tier2.passed:
                case_classification = self.classify_event_case(event_data, {'tier1': tier1, 'tier2': tier2, 'tier3': None})

                return ValidationReport(
                    event_id=event_id,
                    target_platform=target_platform,
                    tier1=tier1,
                    tier2=tier2,
                    tier3=ValidationTier(3, False, "Skipped due to Tier 2 failure"),
                    overall_result=ValidationResult.REJECTED,
                    case_classification=case_classification,
                    content_hash="",
                    rejection_reason=tier2.description
                )

            # Generate content hash for Tier 3
            event_date = None
            event_time = None

            if event_data.get('is_all_day'):
                event_date = datetime.strptime(event_data.get('start_date'), '%Y-%m-%d').date() if event_data.get('start_date') else None
            else:
                start_datetime = datetime.fromisoformat(event_data.get('start_datetime').replace('Z', '+00:00')) if event_data.get('start_datetime') else None
                if start_datetime:
                    event_date = start_datetime.date()
                    event_time = start_datetime.time()

            content_hash = self.generate_content_hash(
                event_data.get('title', ''),
                event_date,
                event_time
            )

            # Tier 3: Duplicate content check
            tier3 = self.tier3_duplicate_content_check(user_id, target_platform, content_hash, event_data)

            # Determine overall result
            overall_result = ValidationResult.APPROVED if tier3.passed else ValidationResult.REJECTED

            # Classify the case
            case_classification = self.classify_event_case(event_data, {
                'tier1': tier1, 'tier2': tier2, 'tier3': tier3
            })

            rejection_reason = None if overall_result == ValidationResult.APPROVED else tier3.description

            # Create validation report
            report = ValidationReport(
                event_id=event_id,
                target_platform=target_platform,
                tier1=tier1,
                tier2=tier2,
                tier3=tier3,
                overall_result=overall_result,
                case_classification=case_classification,
                content_hash=content_hash,
                rejection_reason=rejection_reason
            )

            # Record validation attempt in database
            validation_id = self.record_validation_attempt(user_id, calendar_id, report)
            report.validation_id = validation_id

            print(f"📊 [VALIDATION] Validation complete: {overall_result.value} ({case_classification.value})")
            return report

        except Exception as e:
            print(f"❌ [VALIDATION] Validation failed: {e}")
            # Return error validation report
            return ValidationReport(
                event_id=event_id,
                target_platform=target_platform,
                tier1=ValidationTier(1, False, f"Validation error: {str(e)}", {'error': str(e)}),
                tier2=ValidationTier(2, False, "Skipped due to error"),
                tier3=ValidationTier(3, False, "Skipped due to error"),
                overall_result=ValidationResult.REJECTED,
                case_classification=CaseClassification.MISSING_EVENT,
                content_hash="",
                rejection_reason=f"Validation error: {str(e)}"
            )

    def record_validation_attempt(self, user_id: str, calendar_id: str, report: ValidationReport) -> Optional[str]:
        """Record validation attempt in database"""
        try:
            print(f"📝 [VALIDATION] Recording validation attempt for event {report.event_id}")

            # Get event details for recording
            event_result = self.supabase.table('calendar_events').select(
                'title, start_datetime, end_datetime, start_date, is_all_day'
            ).eq('id', report.event_id).execute()

            if not event_result.data:
                print(f"⚠️ [VALIDATION] Could not find event data for recording")
                return None

            event = event_result.data[0]

            # Prepare normalized title and date/time
            normalized_title = event.get('title', '').lower().strip()

            if event.get('is_all_day'):
                event_date = datetime.strptime(event.get('start_date'), '%Y-%m-%d').date() if event.get('start_date') else None
                event_start_time = None
            else:
                start_datetime = datetime.fromisoformat(event.get('start_datetime').replace('Z', '+00:00')) if event.get('start_datetime') else None
                event_date = start_datetime.date() if start_datetime else None
                event_start_time = start_datetime.time() if start_datetime else None

            # Insert validation record
            validation_data = {
                'user_id': user_id,
                'calendar_id': calendar_id,
                'source_event_id': report.event_id,
                'target_platform': report.target_platform,
                'tier1_db_check': report.tier1.passed,
                'tier2_trash_check': report.tier2.passed,
                'tier3_duplicate_check': report.tier3.passed,
                'content_hash': report.content_hash,
                'normalized_title': normalized_title,
                'event_date': event_date.isoformat() if event_date else None,
                'event_start_time': event_start_time.isoformat() if event_start_time else None,
                'validation_status': report.overall_result.value,
                'rejection_reason': report.rejection_reason,
                'case_classification': report.case_classification.value
            }

            result = self.supabase.table('event_validation_history').insert(validation_data).execute()

            if result.data:
                validation_id = result.data[0]['id']
                print(f"✅ [VALIDATION] Recorded validation attempt: {validation_id}")

                # If validation passed, create content fingerprint
                if report.overall_result == ValidationResult.APPROVED:
                    self.create_content_fingerprint(user_id, report, event_date, event_start_time)

                return validation_id

        except Exception as e:
            print(f"❌ [VALIDATION] Error recording validation attempt: {e}")

        return None

    def create_content_fingerprint(self, user_id: str, report: ValidationReport,
                                   event_date: date, event_start_time: Optional[time]):
        """Create content fingerprint for approved events"""
        try:
            fingerprint_data = {
                'user_id': user_id,
                'platform': report.target_platform,
                'content_hash': report.content_hash,
                'normalized_title': report.tier1.details['event_data'].get('title', '').lower().strip(),
                'event_date': event_date.isoformat() if event_date else None,
                'event_start_time': event_start_time.isoformat() if event_start_time else None,
                'source_event_id': report.event_id,
                'is_active': True
            }

            # Insert with conflict resolution (upsert)
            result = self.supabase.table('event_content_fingerprints').upsert(
                fingerprint_data,
                on_conflict='user_id,platform,content_hash'
            ).execute()

            if result.data:
                print(f"✅ [VALIDATION] Created content fingerprint for future duplicate detection")

        except Exception as e:
            print(f"⚠️ [VALIDATION] Error creating content fingerprint: {e}")

    def validate_event_batch(self, user_id: str, event_ids: List[str], target_platform: str,
                             trashed_events: List[Dict] = None) -> List[ValidationReport]:
        """Validate multiple events in batch"""
        try:
            print(f"📦 [VALIDATION] Starting batch validation: {len(event_ids)} events → {target_platform}")

            reports = []
            approved_count = 0
            rejected_count = 0

            for event_id in event_ids:
                report = self.validate_event_for_sync(user_id, event_id, target_platform, trashed_events)
                reports.append(report)

                if report.overall_result == ValidationResult.APPROVED:
                    approved_count += 1
                else:
                    rejected_count += 1

            print(f"📊 [VALIDATION] Batch validation complete: {approved_count} approved, {rejected_count} rejected")
            return reports

        except Exception as e:
            print(f"❌ [VALIDATION] Batch validation failed: {e}")
            return []

    def get_validation_summary(self, reports: List[ValidationReport]) -> Dict:
        """Generate summary statistics from validation reports"""
        try:
            total_events = len(reports)
            approved_events = [r for r in reports if r.overall_result == ValidationResult.APPROVED]
            rejected_events = [r for r in reports if r.overall_result == ValidationResult.REJECTED]

            # Count by case classification
            case_counts = {}
            for report in reports:
                case = report.case_classification.value
                case_counts[case] = case_counts.get(case, 0) + 1

            # Count by rejection reason
            rejection_reasons = {}
            for report in rejected_events:
                reason = report.rejection_reason or "Unknown"
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

            summary = {
                'total_events': total_events,
                'approved_count': len(approved_events),
                'rejected_count': len(rejected_events),
                'approval_rate': (len(approved_events) / total_events * 100) if total_events > 0 else 0,
                'case_classifications': case_counts,
                'rejection_reasons': rejection_reasons,
                'approved_events': [r.event_id for r in approved_events],
                'rejected_events': [{'event_id': r.event_id, 'reason': r.rejection_reason} for r in rejected_events]
            }

            print(f"📈 [VALIDATION] Summary: {summary['approval_rate']:.1f}% approval rate ({len(approved_events)}/{total_events})")
            return summary

        except Exception as e:
            print(f"❌ [VALIDATION] Error generating summary: {e}")
            return {'error': str(e)}

# Create singleton instance
event_validator = EventValidationService()