from __future__ import annotations


class DomainError(Exception):
    """Base exception for domain-level calculation errors."""


class ValidationError(DomainError):
    """Raised when an input value is invalid for the requested calculation."""


class UnsupportedTrackTypeError(DomainError):
    """Raised when the track type is unknown to the Phase 1 engine."""


class MissingFieldError(ValidationError):
    """Raised when a required field for a track type is missing."""


class ScenarioError(DomainError):
    """Base exception for scenario-generation and recommendation errors."""


class InvalidScenarioInputError(ScenarioError, ValidationError):
    """Raised when a scenario input is invalid for the requested analysis."""


class ScenarioGenerationLimitError(ScenarioError):
    """Raised when scenario generation would exceed the configured safe limit."""


class MissingMarketInputError(ScenarioError, MissingFieldError):
    """Raised when a scenario requires market inputs that were not supplied."""


class MarketDataError(DomainError):
    """Base exception for market-data ingestion, normalization, and lookup."""


class MarketDataFetchError(MarketDataError):
    """Raised when a market-data provider fetch fails."""


class MarketDataParseError(MarketDataError):
    """Raised when a provider payload cannot be parsed."""


class MarketDataValidationError(MarketDataError, ValidationError):
    """Raised when normalized market data fails validation."""


class MarketDataStaleError(MarketDataError):
    """Raised when required market data exists but is too stale for safe use."""


class MarketDataNotFoundError(MarketDataError):
    """Raised when required market data is not available."""


class MarketDataBucketLookupError(MarketDataError):
    """Raised when a mortgage-rate bucket cannot be resolved deterministically."""


class CostEngineError(DomainError):
    """Base exception for refinance cost and penalty calculations."""


class MissingPenaltyInputError(CostEngineError, MissingFieldError):
    """Raised when a penalty-applicable track is missing required inputs."""


class InvalidYearsSinceOriginationError(CostEngineError, ValidationError):
    """Raised when the years-since-origination input is invalid."""


class UnsupportedAdjustablePenaltyCaseError(CostEngineError):
    """Raised when an adjustable-track penalty cannot be computed safely."""


class PaymentStreamError(CostEngineError, ValidationError):
    """Raised when a remaining-payment stream cannot be built or validated."""
