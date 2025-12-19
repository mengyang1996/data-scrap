import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import imageio.v2 as imageio
import os
from collections import Counter
from analysis import preprocess_title

# --- CONFIGURATION ---
conference = "kdd"
INPUT_FILE = f"datasets/{conference}_papers_2015_2025.csv"
OUTPUT_GIF = f"gifs/{conference}_titles_wordcloud.gif"
TEMP_DIR = "temp_frames"

def main():
    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: '{INPUT_FILE}' not found. Please run the scraper first.")
        return
    
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} papers.")

    # 2. Setup Output Directory
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    years = sorted(df['Year'].unique())
    frames = []

    print("Generating word clouds per year...")
    
    for year in years:
        df_year = df[df['Year'] == year]
        
        # Collect all tokens for this year using the shared preprocessing logic
        all_words = []
        for title in df_year['Title'].dropna():
            # preprocess_title returns a list of tokens
            tokens = preprocess_title(title)
            all_words.extend(tokens)
            
        if not all_words:
            print(f"Skipping {year} (no words found)")
            continue
            
        # Count frequencies to respect the tokenization (keeping hyphens etc.)
        word_counts = Counter(all_words)
        
        # Generate WordCloud
        # generate_from_frequencies takes a dict {word: count}
        wc = WordCloud(
            width=800, 
            height=400, 
            background_color='white', 
            colormap='viridis',
            max_words=100
        ).generate_from_frequencies(word_counts)
        
        # Plotting
        plt.figure(figsize=(10, 5))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title(f"{conference.upper()} {year} Top Keywords", fontsize=20)
        plt.tight_layout(pad=1)
        
        # Save frame
        frame_path = os.path.join(TEMP_DIR, f"frame_{conference}_{year}.png")
        plt.savefig(frame_path, dpi=100)
        plt.close()
        
        frames.append(frame_path)
        print(f" - Generated frame for {year}")

    # 3. Create GIF
    if frames:
        print(f"Assembling GIF ({len(frames)} frames)...")
        images = [imageio.imread(f) for f in frames]
        # duration is in seconds per frame
        imageio.mimsave(OUTPUT_GIF, images, duration=2500, loop=0)
        
        print(f"Saved GIF to {os.path.abspath(OUTPUT_GIF)}")
    else:
        print("No frames generated.")

    # 4. Frames preserved
    print(f"Individual frames saved in: {os.path.abspath(TEMP_DIR)}")

if __name__ == "__main__":
    main()