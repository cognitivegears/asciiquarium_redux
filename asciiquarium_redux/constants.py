"""
Constants module for Asciiquarium Redux

This module centralizes all magic numbers and configuration constants used throughout
the application, organized by functional category for better maintainability.
"""

# =============================================================================
# PHYSICS AND MOVEMENT CONSTANTS
# =============================================================================

# Movement multipliers and timing
MOVEMENT_MULTIPLIER = 20.0          # Standard dt multiplier for entity movement
MAX_DELTA_TIME = 0.1                # Maximum allowed delta time per frame

# Fish movement physics
FISH_DEFAULT_SPEED_MIN = 0.6        # Minimum fish swimming speed
FISH_DEFAULT_SPEED_MAX = 2.5        # Maximum fish swimming speed

# Shark movement
SHARK_SPEED = 2.0                   # Base shark swimming speed

# Fishhook movement
FISHHOOK_SPEED = 15.0               # Speed of fishhook lowering/retracting


# =============================================================================
# ANIMATION AND TIMING CONSTANTS
# =============================================================================

# Seaweed animation
SEAWEED_ANIMATION_STEP = 0.25       # Time step for seaweed sway animation
SEAWEED_SWAY_SPEED_MIN = 0.05       # Minimum sway speed to prevent division by zero

# Fish animation and behavior
FISH_BUBBLE_INTERVAL_MIN = 1.5      # Minimum time between fish bubbles
FISH_BUBBLE_INTERVAL_MAX = 4.0      # Maximum time between fish bubbles
FISH_BUBBLE_DEFAULT_MIN = 2.0       # Default minimum bubble interval
FISH_BUBBLE_DEFAULT_MAX = 5.0       # Default maximum bubble interval

# Fish turning animation
FISH_TURN_SHRINK_DURATION = 0.35    # Seconds for fish shrinking phase during turn
FISH_TURN_EXPAND_DURATION = 0.35    # Seconds for fish expanding phase during turn
FISH_TURN_COOLDOWN_MIN = 4.0        # Minimum time before fish can turn again
FISH_TURN_COOLDOWN_MAX = 10.0       # Maximum time before fish can turn again

# Fishhook timing
FISHHOOK_IMPACT_PAUSE_DURATION = 0.35   # Pause after hook impact to show splat
FISHHOOK_DWELL_TIME_DEFAULT = 20.0      # Default time hook dwells at bottom

# Seaweed lifecycle timing
SEAWEED_SWAY_SPEED_MIN_RANGE = 0.18     # Minimum sway speed in range
SEAWEED_SWAY_SPEED_MAX_RANGE = 0.5      # Maximum sway speed in range
SEAWEED_LIFETIME_MIN = 25.0             # Minimum seaweed lifetime
SEAWEED_LIFETIME_MAX = 60.0             # Maximum seaweed lifetime
SEAWEED_REGROW_DELAY_MIN = 4.0          # Minimum regrow delay
SEAWEED_REGROW_DELAY_MAX = 12.0         # Maximum regrow delay
SEAWEED_GROWTH_RATE_MIN = 6.0           # Minimum growth rate (rows/sec)
SEAWEED_GROWTH_RATE_MAX = 12.0          # Maximum growth rate (rows/sec)
SEAWEED_SHRINK_RATE_MIN = 8.0           # Minimum shrink rate (rows/sec)
SEAWEED_SHRINK_RATE_MAX = 16.0          # Maximum shrink rate (rows/sec)
SEAWEED_LIFETIME_STAGGER_FRACTION = 0.4 # Fraction of lifetime used for initial stagger


# =============================================================================
# LAYOUT AND POSITIONING CONSTANTS
# =============================================================================

# Screen area calculations
SCREEN_WIDTH_UNIT_DIVISOR = 80.0    # Base screen width for unit calculations
FISH_DENSITY_AREA_DIVISOR = 350     # Area divisor for fish count calculation
SEAWEED_DENSITY_WIDTH_DIVISOR = 15  # Width divisor for seaweed count calculation

# Depth and positioning limits
FISHHOOK_DEPTH_LIMIT_FRACTION = 0.75    # Fraction of screen height for hook depth


# =============================================================================
# COLLISION AND ENTITY CONSTANTS
# =============================================================================

# Shark collision offsets (maintain exact parity with original Perl implementation)
SHARK_TEETH_OFFSET_RIGHT_X = 44     # X offset for right-moving shark teeth collision
SHARK_TEETH_OFFSET_RIGHT_Y = 7      # Y offset for right-moving shark teeth collision
SHARK_TEETH_OFFSET_LEFT_X = 9       # X offset for left-moving shark teeth collision
SHARK_TEETH_OFFSET_LEFT_Y = 7       # Y offset for left-moving shark teeth collision

# Fishhook collision
FISHHOOK_TIP_OFFSET_X = 1           # X offset from hook base to tip
FISHHOOK_TIP_OFFSET_Y = 2           # Y offset from hook base to tip


# =============================================================================
# ENTITY GENERATION CONSTANTS
# =============================================================================

# Seaweed generation
SEAWEED_HEIGHT_MIN = 3              # Minimum seaweed height
SEAWEED_HEIGHT_MAX = 6              # Maximum seaweed height
SEAWEED_PHASE_MAX = 1               # Maximum phase value for seaweed animation

# Fish generation and respawn
FISH_MINIMUM_COUNT = 2              # Minimum number of fish to maintain


# =============================================================================
# RENDERING CONSTANTS
# =============================================================================

# Fishhook line rendering
FISHHOOK_LINE_CHAR = "|"            # Character used for fishhook line
FISHHOOK_LINE_TOP = -50             # Top Y position for fishhook line
FISHHOOK_LINE_OFFSET_X = 7          # X offset for fishhook line from hook base
