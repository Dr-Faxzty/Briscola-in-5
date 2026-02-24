class GameError(Exception):
    """Base class for all game-related errors."""


class PhaseError(GameError):
    """Raised when an action is not allowed in the current phase."""


class TurnError(GameError):
    """Raised when a player acts out of turn or in an invalid order."""


class AuctionError(GameError):
    """Raised for invalid auction bids/passes or auction state errors."""


class MoveError(GameError):
    """Raised for invalid moves (e.g., illegal card played)."""
