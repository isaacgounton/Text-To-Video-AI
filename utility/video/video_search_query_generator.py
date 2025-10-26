from openai import OpenAI
import os
import json
import re
from datetime import datetime
from utility.utils import log_response,LOG_TYPE_GPT

if len(os.environ.get("GROQ_API_KEY")) > 30:
    from groq import Groq
    model = "moonshotai/kimi-k2-instruct-0905"
    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
        )
else:
    model = "gpt-4o"
    OPENAI_API_KEY = os.environ.get('OPENAI_KEY')
    client = OpenAI(api_key=OPENAI_API_KEY)

log_directory = ".logs/gpt_logs"

# SEGMENT DURATION CONFIGURATION
# These settings control how many segments are created for the video
# Longer segments = fewer API calls to Pexels = less rate limiting
# Adjust these values based on your needs:
# - "2-4 seconds": More segments, more dynamic but more API calls
# - "3-5 seconds": Balanced (current setting)
# - "5-7 seconds": Fewer segments, fewer API calls, less dynamic
# See VIDEO_GENERATION_EXPLAINED.md for more details

prompt = """# Instructions

Given the following video script and timed captions, extract three visually concrete and specific keywords for each time segment that can be used to search for background videos. The keywords should be short and capture the main essence of the sentence. They can be synonyms or related terms. If a caption is vague or general, consider the next timed caption for more context. If a keyword is a single word, try to return a two-word keyword that is visually concrete. If a time frame contains two or more important pieces of information, divide it into shorter time frames with one keyword each. Ensure that the time periods are strictly consecutive and cover the entire length of the video. Each keyword should cover between 3-5 seconds (longer segments are better). Minimize the number of segments - aim for fewer, longer segments rather than many short ones. The output should be in JSON format, like this: [[[t1, t2], ["keyword1", "keyword2", "keyword3"]], [[t2, t3], ["keyword4", "keyword5", "keyword6"]], ...]. Please handle all edge cases, such as overlapping time segments, vague or general captions, and single-word keywords.

For example, if the caption is 'The cheetah is the fastest land animal, capable of running at speeds up to 75 mph', the keywords should include 'cheetah running', 'fastest animal', and '75 mph'. Similarly, for 'The Great Wall of China is one of the most iconic landmarks in the world', the keywords should be 'Great Wall of China', 'iconic landmark', and 'China landmark'.

Important Guidelines:

Use only English in your text queries.
Each search string must depict something visual.
The depictions have to be extremely visually concrete, like rainy street, or cat sleeping.
'emotional moment' <= BAD, because it doesn't depict something visually.
'crying child' <= GOOD, because it depicts something visual.
The list must always contain the most relevant and appropriate query searches.
['Car', 'Car driving', 'Car racing', 'Car parked'] <= BAD, because it's 4 strings.
['Fast car'] <= GOOD, because it's 1 string.
['Un chien', 'une voiture rapide', 'une maison rouge'] <= BAD, because the text query is NOT in English.

Note: Your response should be the response only and no extra text or data.
  """

def fix_json(json_str):
    """Clean and fix JSON string to handle various formatting issues"""
    # Remove any markdown code blocks
    json_str = json_str.replace("```json", "").replace("```", "")
    
    # Replace typographical apostrophes with straight quotes
    json_str = json_str.replace("'", "'")
    
    # Replace any incorrect quotes (e.g., mixed single and double quotes)
    json_str = json_str.replace(""", "\"").replace(""", "\"").replace("'", "\"").replace("'", "\"")
    
    # Add escaping for quotes within the strings
    json_str = json_str.replace('"you didn"t"', '"you didn\'t"')
    
    # Fix numpy types: np.float64(X) -> X
    json_str = re.sub(r'np\.float64\(([\d.]+)\)', r'\1', json_str)
    json_str = re.sub(r'np\.int64\((\d+)\)', r'\1', json_str)
    json_str = re.sub(r'np\.float32\(([\d.]+)\)', r'\1', json_str)
    
    # Remove any remaining numpy type notations
    json_str = json_str.replace("np.float64(", "").replace("np.int64(", "").replace("np.float32(", "")
    
    # Remove trailing commas that might appear before ] or }
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    return json_str.strip()

def getVideoSearchQueriesTimed(script,captions_timed):
    end = captions_timed[-1][0][1]
    try:
        
        out = [[[0,0],""]]
        while out[-1][0][1] != end:
            content = call_OpenAI(script,captions_timed).replace("'",'"')
            try:
                out = json.loads(content)
            except json.JSONDecodeError as e:
                print("JSON decode error:", str(e))
                print("Raw content: \n", content, "\n\n")
                
                # Try to fix the JSON
                cleaned_content = fix_json(content)
                print("Cleaned content: \n", cleaned_content, "\n\n")
                
                try:
                    out = json.loads(cleaned_content)
                except json.JSONDecodeError as e2:
                    print("Failed to parse even after cleaning:", str(e2))
                    print("This might be a Groq/OpenAI API issue. Retrying...")
                    # Return None to trigger retry
                    return None
            except Exception as e:
                print("Unexpected error:", str(e))
                return None
                
        return out
    except Exception as e:
        print("error in response",e)
        import traceback
        traceback.print_exc()
   
    return None

def call_OpenAI(script,captions_timed):
    user_content = """Script: {}
Timed Captions:{}
""".format(script,"".join(map(str,captions_timed)))
    print("Content", user_content)
    
    response = client.chat.completions.create(
        model= model,
        temperature=1,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_content}
        ]
    )
    
    text = response.choices[0].message.content.strip()
    text = re.sub(r'\s+', ' ', text)
    print("Text", text)
    log_response(LOG_TYPE_GPT,script,text)
    return text

def merge_empty_intervals(segments):
    merged = []
    i = 0
    while i < len(segments):
        interval, url = segments[i]
        if url is None:
            # Find consecutive None intervals
            j = i + 1
            while j < len(segments) and segments[j][1] is None:
                j += 1
            
            # Merge consecutive None intervals with the previous valid URL
            if i > 0:
                prev_interval, prev_url = merged[-1]
                if prev_url is not None and prev_interval[1] == interval[0]:
                    merged[-1] = [[prev_interval[0], segments[j-1][0][1]], prev_url]
                else:
                    merged.append([interval, prev_url])
            else:
                merged.append([interval, None])
            
            i = j
        else:
            merged.append([interval, url])
            i += 1
    
    return merged
