import os 
import requests
import time
import hashlib
from utility.utils import log_response,LOG_TYPE_PEXEL

PEXELS_API_KEY = os.environ.get('PEXELS_KEY')
REQUEST_DELAY = 0.5  # Delay between requests in seconds (500ms)

# Simple in-memory cache for API responses
_api_cache = {}

def search_videos(query_string, orientation_landscape=True):
    """Search videos with caching to avoid duplicate API calls"""
    
    # Create cache key from query and orientation
    cache_key = hashlib.md5(f"{query_string}_{orientation_landscape}".encode()).hexdigest()
    
    # Check cache first
    if cache_key in _api_cache:
        print(f"🔄 Using cached result for query: '{query_string}'")
        return _api_cache[cache_key]
   
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    # Add delay to avoid rate limiting
    time.sleep(REQUEST_DELAY)
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_count = 0
    retry_delay = 2  # Start with 2 seconds
    
    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            # Check for HTTP errors
            if response.status_code == 429:  # Too Many Requests
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Rate limited (429). Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff: 2s, 4s, 8s
                    continue
                else:
                    print(f"ERROR: Rate limited after {max_retries} retries. Please try again later.")
                    result = {"error": "HTTP 429", "message": "Rate limited - Max retries exceeded"}
                    _api_cache[cache_key] = result
                    return result
            
            elif response.status_code != 200:
                print(f"ERROR: Pexels API returned status code {response.status_code}")
                print(f"Response: {response.text}")
                result = {"error": f"HTTP {response.status_code}", "message": response.text}
                _api_cache[cache_key] = result
                return result
            
            # Success - cache and return
            json_data = response.json()
            _api_cache[cache_key] = json_data
            log_response(LOG_TYPE_PEXEL, query_string, response.json())
            return json_data
            
        except requests.exceptions.Timeout:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Request timeout. Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print("ERROR: Request timeout after max retries")
                result = {"error": "Timeout", "message": "Request timed out"}
                _api_cache[cache_key] = result
                return result
        except Exception as e:
            print(f"ERROR: Exception during API call: {str(e)}")
            result = {"error": "Exception", "message": str(e)}
            _api_cache[cache_key] = result
            return result
    
    result = {"error": "Unknown", "message": "Unknown error occurred"}
    _api_cache[cache_key] = result
    return result


def getBestVideo(query_string, orientation_landscape=True, used_vids=[]):
    vids = search_videos(query_string, orientation_landscape)
    
    # Check if the API response contains the expected 'videos' key
    if 'videos' not in vids:
        error_msg = vids.get('error', 'Unknown error from Pexels API')
        print(f"ERROR: Pexels API returned error: {error_msg}")
        print(f"Full response: {vids}")
        return None
    
    videos = vids['videos']  # Extract the videos list from JSON

    # Filter and extract videos with width and height as 1920x1080 for landscape or 1080x1920 for portrait
    if orientation_landscape:
        filtered_videos = [video for video in videos if video['width'] >= 1920 and video['height'] >= 1080 and video['width']/video['height'] == 16/9]
    else:
        filtered_videos = [video for video in videos if video['width'] >= 1080 and video['height'] >= 1920 and video['height']/video['width'] == 16/9]

    # Sort the filtered videos by duration in ascending order
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15-int(x['duration'])))

    # Extract the top 3 videos' URLs
    for video in sorted_videos:
        for video_file in video['video_files']:
            if orientation_landscape:
                if video_file['width'] == 1920 and video_file['height'] == 1080:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
            else:
                if video_file['width'] == 1080 and video_file['height'] == 1920:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
    print("NO LINKS found for this round of search with query :", query_string)
    return None


def generate_video_url(timed_video_searches, video_server):
    """Generate video URLs with smart keyword selection and video reuse"""
    timed_video_urls = []
    if video_server == "pexel":
        used_links = []
        total_searches = len(timed_video_searches)
        last_found_url = None  # Reuse videos for consecutive segments
        reuse_count = 0
        REUSE_LIMIT = 2  # Reuse each video for up to 2-3 segments
        
        for idx, (time_interval, search_terms) in enumerate(timed_video_searches):
            t1, t2 = time_interval
            url = None
            attempted_queries = []
            
            # Check if we should reuse the last video
            if last_found_url and reuse_count < REUSE_LIMIT:
                url = last_found_url
                reuse_count += 1
                print(f"[{idx+1}/{total_searches}] ♻️  Reusing video (Segment {reuse_count}/{REUSE_LIMIT})")
            else:
                # Try each keyword, but be smart about it
                for query in search_terms:
                    attempted_queries.append(query)
                    print(f"[{idx+1}/{total_searches}] Searching for: '{query}' (Time: {t1}-{t2}s)")
                    
                    url = getBestVideo(query, orientation_landscape=True, used_vids=used_links)
                    if url:
                        print(f"  ✅ Found video for '{query}'")
                        used_links.append(url.split('.hd')[0])
                        last_found_url = url
                        reuse_count = 0  # Reset reuse counter
                        break
                    else:
                        print(f"  ❌ No video found for '{query}'")
                
                if url is None and attempted_queries:
                    print(f"⚠️  Warning: No video found for any of these queries: {attempted_queries}")
                    # Fallback: reuse last found video if available
                    if last_found_url:
                        url = last_found_url
                        print(f"  Using fallback: last found video")
            
            timed_video_urls.append([[t1, t2], url])
            
        print(f"\n📊 Summary: Made {len(_api_cache)} unique API calls with caching and reuse")
        
    elif video_server == "stable_diffusion":
        timed_video_urls = get_images_for_video(timed_video_searches)

    return timed_video_urls
