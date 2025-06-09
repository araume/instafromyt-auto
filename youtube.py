import os
import datetime
from googleapiclient.discovery import build
import yt_dlp
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')  # Get from https://console.developers.google.com/
SEARCH_QUERY = 'trending'  # or any topic/keyword
MAX_RESULTS = 10           # Number of videos to analyze/download
DAYS_AGO = 1               # How many days back to look

# --- SETUP YOUTUBE API ---
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_shorts_videos(query, published_after, max_results=10):
    # Search for videos matching the query and published after a certain date
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        type='video',
        maxResults=max_results*2,  # Get more to filter later
        publishedAfter=published_after,
        videoDuration='short'
    ).execute()

    video_ids = [item['id']['videoId'] for item in search_response['items']]
    # Get video statistics
    videos_response = youtube.videos().list(
        part='snippet,statistics',
        id=','.join(video_ids)
    ).execute()

    # Filter for Shorts (vertical, <60s, #Shorts in title/desc)
    shorts = []
    for item in videos_response['items']:
        title = item['snippet']['title'].lower()
        desc = item['snippet']['description'].lower()
        if 'shorts' in title or 'shorts' in desc:
            stats = item['statistics']
            shorts.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'comments': int(stats.get('commentCount', 0)),
                'url': f"https://www.youtube.com/shorts/{item['id']}"
            })
    return shorts

def rank_videos(videos):
    # Rank by views, likes, comments (simple weighted sum)
    for v in videos:
        v['score'] = v['views'] + 5*v['likes'] + 10*v['comments']
    return sorted(videos, key=lambda x: x['score'], reverse=True)

def download_video(url, output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    # Calculate date range
    today = datetime.datetime.utcnow()
    published_after = (today - datetime.timedelta(days=DAYS_AGO)).isoformat("T") + "Z"
    print(f"Searching for shorts since {published_after}...")

    shorts = get_shorts_videos(SEARCH_QUERY, published_after, MAX_RESULTS)
    if not shorts:
        print("No shorts found.")
        return

    ranked = rank_videos(shorts)[:MAX_RESULTS]
    print("Top Shorts:")
    for idx, v in enumerate(ranked, 1):
        print(f"{idx}. {v['title']} | Views: {v['views']} | Likes: {v['likes']} | Comments: {v['comments']}")
        print(f"   {v['url']}")

    print("\nDownloading top videos...")
    for v in ranked:
        print(f"Downloading: {v['title']}")
        download_video(v['url'])

if __name__ == "__main__":
    main()
