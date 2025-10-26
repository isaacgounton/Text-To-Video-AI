# Video Generation Architecture Explained 🎬

## Question 1: Search Query Requirements

### No, you're NOT obliged to use 2-word queries

The prompt says:
> "If a keyword is a single word, try to return a two-word keyword"

This is just a **suggestion to improve search quality**, not a rule.

**Valid query lengths:**

- ✅ Single word: `"cells"`, `"water"`, `"fire"`
- ✅ Two words: `"cell production"`, `"party popper"` (recommended)
- ✅ Three+ words: `"microscopic cells multiplying"`, `"cell mitosis under microscope"`
- ✅ Numbers: `"25 million"`, `"75 mph"`

**The ONLY real rule:**
> "Each search string must depict something visual"

**Good:** `"crying child"`, `"rainy street"`, `"cells dividing"`
**Bad:** `"emotional moment"`, `"important discovery"` (too vague)

### To Customize the Prompt

Edit `/utility/video/video_search_query_generator.py` around line 25:

```python
prompt = """# Instructions
...
If a keyword is a single word, try to return a **two-to-three word keyword** that is visually concrete.
...
"""
```

---

## Question 2: Why So Many Background Videos?

### Understanding the Architecture

Your app creates a **dynamic, segment-based video** not a single-background video:

```
INPUT: 1 topic (e.g., "Human Cell Facts")
       ↓
PROCESSING:
[1] Generate Script (AI)
    → "Red blood cells produce 2 million new cells per second..."
    
[2] Convert to Captions with Timestamps
    → (0.0-1.5): "Red blood cells"
    → (1.5-2.8): "produce 2 million"
    → (2.8-3.5): "new cells per second"
    → ... (repeated for entire video)
    
[3] Generate Keywords for Each Caption Segment
    → (0.0-1.5): ["red blood cells", "blood cell closeup", "cell under microscope"]
    → (1.5-2.8): ["cell production", "25 million", "cells dividing"]
    → (2.8-3.5): ["cell birth", "new cells", "cellular growth"]
    
[4] Search for 1 Video Per Segment
    → Segment 1: Find video of "red blood cells"
    → Segment 2: Find video of "cell production"
    → Segment 3: Find video of "new cells"
    → ... (57 videos total)

OUTPUT: Composite video with:
├── Segment 1 (0-1.5s): Red blood cell video + voice-over
├── Segment 2 (1.5-2.8s): Cell production video + voice-over
├── Segment 3 (2.8-3.5s): New cells video + voice-over
└── ... (57 segments total)
```

### Why This Approach?

✅ **Pros:**

- Keeps viewers engaged with changing visuals
- Perfect for YouTube Shorts format
- Relevant background for each phrase
- Professional, dynamic feel

❌ **Cons:**

- Requires many videos (~57 per minute)
- More API calls to Pexels
- Takes longer to generate
- Rate limiting risk

---

## Solutions to Reduce API Calls & Improve Performance 🚀

### **Solution 1: Video Reuse (Already Implemented)** ♻️

**What it does:**
Reuses the same video for 2-3 consecutive segments instead of searching for a new one every time.

**Example:**

```
Old way (57 API calls):
Segment 1: Search for "cell production" → Found ✅
Segment 2: Search for "25 million" → Found ✅
Segment 3: Search for "new cells" → Found ✅

New way (20-30 API calls):
Segment 1: Search for "cell production" → Found ✅
Segment 2: ♻️ REUSE "cell production" video
Segment 3: ♻️ REUSE "cell production" video
Segment 4: Search for "25 million" → Found ✅
Segment 5: ♻️ REUSE "25 million" video
...
```

**You'll see:**

```
[1/57] Searching for: 'cell production' (Time: 0.0-1.5s)
  ✅ Found video for 'cell production'
[2/57] ♻️  Reusing video (Segment 1/2)
[3/57] ♻️  Reusing video (Segment 2/2)
[4/57] Searching for: '25 million' (Time: 2.8-3.5s)
  ✅ Found video for '25 million'
```

**Expected reduction:** 60-70% fewer API calls ✅

### **Solution 2: Segment Duration Adjustment**

Increase segment duration from 1-2 seconds to 3-4 seconds:

**Before:** 57 segments for 60 seconds
**After:** 20-30 segments for 60 seconds

Edit `/utility/video/video_search_query_generator.py` line 29:

```python
# Change from:
# Each keyword should cover between 2-4 seconds

# To:
# Each keyword should cover between 3-5 seconds
```

**Expected reduction:** 50-60% fewer segments needed

### **Solution 3: Cache Across Sessions**

Current caching only works within one video generation. Add persistent cache:

```python
# In background_video_generator.py
import pickle

def save_cache():
    with open(".cache/video_cache.pkl", "wb") as f:
        pickle.dump(_api_cache, f)

def load_cache():
    try:
        with open(".cache/video_cache.pkl", "rb") as f:
            return pickle.load(f)
    except:
        return {}
```

**Expected reduction:** 80%+ if generating similar videos

---

## Recommended Configuration

### For Best Performance

**File:** `utility/video/background_video_generator.py`

```python
REQUEST_DELAY = 1.0          # Wait 1 second between requests
REUSE_LIMIT = 3              # Reuse videos for up to 3 segments
max_retries = 5              # Try 5 times on rate limit
```

**File:** `utility/video/video_search_query_generator.py`

```python
# Change prompt to:
# "Each keyword should cover between 3-5 seconds"
# Instead of "2-4 seconds"
```

---

## API Usage Comparison

| Approach | Segments | API Calls | Time | Rate Limit Risk |
|----------|----------|-----------|------|-----------------|
| Original | 57 | 170+ | Slow | Very High 🔴 |
| With caching | 57 | 80-100 | Medium | High 🟡 |
| + Video reuse | 57 | 20-30 | Fast | Low 🟢 |
| + Longer segments | 20-30 | 8-15 | Very Fast | Very Low 🟢 |
| All optimizations | 20-30 | 5-10 | Very Fast | Minimal 🟢 |

---

## Current Implementation

✅ **Already enabled:**

- Response caching (same query = no new API call)
- Smart keyword selection (stops after first match)
- Video reuse (♻️ indicator in console)
- Retry backoff (handles 429 errors)
- Request throttling (500ms-1s delays)

**Result:** ~60-70% reduction in API calls

---

## FAQ

**Q: Can I generate longer videos (2+ minutes)?**
A: Yes, but you'll need more API quota. Consider using persistent caching.

**Q: Why not just use 1 background video for entire video?**
A: Possible but looks unprofessional. Your approach is better for engagement.

**Q: Can I batch multiple videos?**
A: Not yet, but would help with API rate limits. Feature suggestion!

**Q: Is there a way to avoid rate limiting completely?**
A: Yes - increase delays or use persistent caching across sessions.
