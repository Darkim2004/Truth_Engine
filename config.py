"""
Truth Engine — Configurazione centralizzata.
"""

# --- Search ---
SEARCH_MAX_RESULTS = 3  # Risultati per motore per query
SEARCH_RETRY_MAX = 3
SEARCH_BACKOFF_FACTOR = 2  # Secondi: 2, 4, 8
SEARCH_DELAY_BETWEEN = 1.5  # Delay tra ricerche successive (secondi)

# --- HTTP Fetching ---
HTTP_TIMEOUT = 15  # Secondi
HTTP_MAX_RETRIES = 3
HTTP_BACKOFF_FACTOR = 2
HTTP_MAX_CONCURRENCY = 10  # Semaphore per richieste parallele

# --- Playwright ---
PLAYWRIGHT_TIMEOUT = 20000  # Millisecondi
PLAYWRIGHT_SCROLL_DELAY = 500  # ms tra scroll
PLAYWRIGHT_SCROLL_STEPS = 5

# --- Headers realistici ---
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# --- URL Normalization ---
TRACKING_PARAMS = {
    # UTM
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "utm_cid",
    # Social / Ads
    "fbclid", "gclid", "gclsrc", "igshid", "mc_cid", "mc_eid",
    "msclkid", "twclid", "ttclid",
    # Referral / tracking
    "ref", "ref_src", "ref_url", "source", "src",
    "_ga", "_gl", "_hsenc", "_hsmi", "_openstat",
    "yclid", "zanpid",
    # Misc
    "amp", "s", "share", "si", "spm",
}

# --- Paywall Detection ---
PAYWALL_KEYWORDS = [
    "subscribe to continue",
    "subscribe to read",
    "premium content",
    "premium article",
    "paywall",
    "sign in to read",
    "login to read",
    "create a free account",
    "become a member",
    "members only",
    "subscriber exclusive",
    "already a subscriber",
    "start your free trial",
    "unlock this article",
    "get unlimited access",
    "this content is for subscribers",
]

PAYWALL_MIN_CONTENT_LENGTH = 300  # Char minimi per considerare il contenuto valido

# --- Evidence Scoring (Chunking + Similarity) ---
CHUNK_MIN_SIZE = 150
CHUNK_MAX_SIZE = 800
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MIN_THRESHOLD = 0.1
EMBEDDING_TOP_K = 3
