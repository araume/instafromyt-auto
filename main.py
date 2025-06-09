import os
from instagrapi import Client
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import torch
from transformers import pipeline

load_dotenv()

USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
VIDEO_DIR = "downloads"

def get_best_post_time():
    # For demo: returns next hour. Replace with your own logic or use analytics.
    now = datetime.now()
    best_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return best_time

def generate_caption(title):
    # Use a small, free model for text generation
    generator = pipeline('text-generation', model='gpt2', device=0 if torch.cuda.is_available() else -1)
    prompt = f"Write a catchy Instagram caption with hashtags for a viral video titled: '{title}'."
    result = generator(prompt, max_length=40, num_return_sequences=1)
    return result[0]['generated_text'].strip()

def main():
    cl = Client()
    cl.login(USERNAME, PASSWORD)

    videos = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.mp4')]
    for video in videos:
        video_path = os.path.join(VIDEO_DIR, video)
        # Use video filename (without extension) as the title
        title = os.path.splitext(video)[0]
        caption = generate_caption(title)

        # Schedule posting at the best time
        best_time = get_best_post_time()
        wait_seconds = (best_time - datetime.now()).total_seconds()
        if wait_seconds > 0:
            print(f"Waiting {int(wait_seconds)} seconds to post {video} at {best_time}")
            time.sleep(wait_seconds)

        print(f"Posting {video} to Instagram with caption: {caption}")
        cl.clip_upload(video_path, caption)
        print(f"Posted {video}!")

if __name__ == "__main__":
    main()
