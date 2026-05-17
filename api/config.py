"""
Central configuration for the TokenWise API.

All tuneable constants live here so they can be adjusted in one place
without hunting through endpoint code.
"""

# Maximum number of characters allowed in a single prompt.
# Requests exceeding this limit are rejected with HTTP 422 before any
# processing occurs, preventing excessive LLM API usage.
MAX_PROMPT_CHARS = 10_000

# Seconds to wait for a response from the upstream LLM (POST /chat).
# Requests that exceed this threshold are cancelled with HTTP 504.
LLM_TIMEOUT_SECONDS = 30
