# API Rate Limiting Optimization 🚀

## Problem Analysis

Your code was being rate limited (HTTP 429) because it was making **too many redundant API requests**.

### Why?

The AI generates **3 keywords per video segment**:

```
"cheetah running", "fast animal", "75 mph speed"
```

The old code tried each keyword individually:

```python
for query in search_terms:  # Try ALL 3 keywords
    url = getBestVideo(query)  # Makes 1 API call PER keyword
```

**With 61 video segments × 3 keywords = 183 API requests!** 🔥

That's why Pexels was rate limiting you.

## Solutions Implemented ✅

### 1. **Response Caching** 💾

- Every API response is now cached by query
- If the same keyword appears in multiple segments, it uses the cached result
- Example: If both segment 1 and segment 5 need "cheetah running", only 1 API call is made

```python
_api_cache = {}  # Stores API responses
cache_key = hashlib.md5(f"{query}_{orientation}".encode()).hexdigest()

if cache_key in _api_cache:
    print(f"🔄 Using cached result for query: '{query}'")
    return _api_cache[cache_key]
```

### 2. **Smart Keyword Selection** 🎯

- The code tries each keyword and **stops after finding a video**
- If keyword 1 ("cheetah running") returns videos, it doesn't try keywords 2 and 3
- Progress tracking shows which queries are being attempted

```python
for query in search_terms:
    url = getBestVideo(query)
    if url:
        print(f"  ✅ Found video for '{query}'")
        break  # Don't try other keywords if this one worked
```

### 3. **Request Throttling** ⏱️

- 500ms delay between requests to spread load
- Exponential backoff on rate limiting: 2s → 4s → 8s
- Prevents hammering the API

```python
time.sleep(0.5)  # 500ms between requests
```

## Expected Results 📊

### Before Optimization

- 183+ API requests for 61 segments
- High rate limiting errors (429)
- Slow video generation
- Wasted API quota

### After Optimization

- ~20-40 API requests (depending on cache hits)
- Few or no rate limiting errors
- Faster video generation
- Much lower API usage

## How Much Better? 📈

If you have similar keywords across segments (e.g., multiple "landscape", "trees", "water" shots):

- **Best case**: ~15-20 API calls (80% reduction)
- **Average case**: ~40-50 API calls (70% reduction)
- **Worst case**: ~80-100 API calls (50% reduction)

## How to Monitor

Watch for these messages in the console:

```
✅ Found video for 'cheetah running'    # First keyword worked
❌ No video found for 'fast animal'     # Second keyword failed
🔄 Using cached result for query: 'trees'  # Cache hit!
Rate limited (429). Retrying in 2 seconds... (Attempt 1/3)  # Retry logic

📊 Summary: Made 35 unique API calls with caching
```

## If You Still Get Rate Limited

Increase the delay or retry attempts in `utility/video/background_video_generator.py`:

```python
REQUEST_DELAY = 1.0  # Increase to 1 second (was 0.5)
max_retries = 5      # Increase attempts (was 3)
retry_delay = 3      # Start with 3 second backoff (was 2)
```

## File Changes

- **Modified**: `utility/video/background_video_generator.py`
  - Added caching system
  - Improved retry logic
  - Better progress tracking
  - Optimized keyword selection

No breaking changes - fully backward compatible! ✅
