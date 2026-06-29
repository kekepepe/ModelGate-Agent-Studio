# Default quota thresholds and configuration
# MVP stage: hard-coded, no user customization

DEFAULT_THRESHOLDS = {
    "warning_percent": 0.70,
    "near_limit_percent": 0.90,
    "cooldown_minutes": 1,
    "max_errors_per_hour": 3,
    "max_rate_limit_errors": 2,
}

# Quota status enum values
QUOTA_STATUS_NORMAL = "normal"
QUOTA_STATUS_WARNING = "warning"
QUOTA_STATUS_NEAR_LIMIT = "near_limit"
QUOTA_STATUS_LIMITED = "limited"
QUOTA_STATUS_COOLDOWN = "cooldown"
QUOTA_STATUS_UNKNOWN = "unknown"

# Quota mode enum values
QUOTA_MODE_KNOWN = "known"
QUOTA_MODE_ESTIMATED = "estimated"
QUOTA_MODE_UNKNOWN = "unknown"

# Error codes that trigger limit_error_count
LIMIT_ERROR_CODES = {429, 403, 402}
RATE_LIMIT_ERROR_CODES = {429, 503, 529}

# Rate limit error subtypes
RATE_LIMIT_SUBTYPES = {"insufficient_quota", "rate_limit_exceeded"}

# Quota health scores for Model Router integration
QUOTA_HEALTH_SCORES = {
    QUOTA_STATUS_NORMAL: 1.0,
    QUOTA_STATUS_WARNING: 0.7,
    QUOTA_STATUS_NEAR_LIMIT: 0.3,
    QUOTA_STATUS_LIMITED: 0.0,
    QUOTA_STATUS_COOLDOWN: 0.0,
    QUOTA_STATUS_UNKNOWN: 0.5,
}
