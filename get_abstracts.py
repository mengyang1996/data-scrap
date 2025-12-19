import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
import random

# --- CONFIGURATION ---
INPUT_FILE = "datasets/neurips_papers_2015_2025.csv"
OUTPUT_FILE = "datasets/neurips_papers_with_abstracts.csv"

class RateLimitException(Exception):
    pass

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:90.0) Gecko/20100101 Firefox/90.0"
]

def get_abstract(url):
    """
    Fetches the abstract from the given URL.
    Tailored for NeurIPS proceedings pages (papers.nips.cc / proceedings.neurips.cc).
    """
    # Skip invalid or PDF links
    if not isinstance(url, str) or len(url) < 5 or url.lower().endswith('.pdf'):
        return None

    try:
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        # Allow redirects because DBLP links often redirect to the actual proceedings page
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        if response.status_code == 429:
            raise RateLimitException("429 Too Many Requests")

        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Strategy 1: Meta Tags (High Precision) ---
        # NeurIPS proceedings usually have <meta name="citation_abstract" content="...">
        meta_desc = soup.find('meta', attrs={'name': 'citation_abstract'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()

        # --- Strategy 2: Header + Paragraph (Heuristic) ---
        # Look for <h4>Abstract</h4> or <h3>Abstract</h3>
        header = soup.find(['h3', 'h4', 'h2'], string=lambda t: t and 'Abstract' in t)
        if header:
            # Case A: The abstract text is in the next <p> sibling
            next_p = header.find_next_sibling('p')
            if next_p:
                return next_p.get_text(strip=True)
            
            # Case B: Sometimes it's in the next <div> sibling
            next_div = header.find_next_sibling('div')
            if next_div:
                return next_div.get_text(strip=True)
                
            # Case C: It might be the next element in the parse tree (find_next)
            next_elem = header.find_next(['p', 'div'])
            if next_elem:
                return next_elem.get_text(strip=True)

        # --- Strategy 3: Class Name (Heuristic) ---
        abstract_elem = soup.find(class_='abstract')
        if abstract_elem:
            return abstract_elem.get_text(strip=True)

        return None

    except Exception as e:
        # print(f"Error fetching {url}: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return

    print(f"Reading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)

    # Initialize Abstract column if not present
    if 'Abstract' not in df.columns:
        df['Abstract'] = None

    # Resume capability: Check if output file exists and load existing abstracts
    if os.path.exists(OUTPUT_FILE):
        print(f"Found existing '{OUTPUT_FILE}'. Attempting to resume...")
        try:
            df_existing = pd.read_csv(OUTPUT_FILE)
            if 'Abstract' in df_existing.columns and 'Link' in df_existing.columns:
                existing_map = df_existing.dropna(subset=['Link', 'Abstract']).set_index('Link')['Abstract'].to_dict()
                df['Abstract'] = df['Link'].map(existing_map).fillna(df['Abstract'])
                print(f"Resumed with {df['Abstract'].notna().sum()} abstracts already loaded.")
        except Exception as e:
            print(f"Warning: Could not read existing output file to resume. Starting fresh. Error: {e}")

    total_papers = len(df)
    print(f"Starting extraction for {total_papers} papers...")

    try:
        for index, row in df.iterrows():
            if pd.notna(row['Abstract']) and str(row['Abstract']).strip():
                continue

            link = row['Link']
            if pd.isna(link) or link == "N/A":
                continue

            print(f"[{index + 1}/{total_papers}] Fetching: {str(row['Title'])[:50]}...")
            abstract = get_abstract(link)
            if abstract:
                df.at[index, 'Abstract'] = abstract
                preview = (abstract[:100].replace('\n', ' ') + '...') if len(abstract) > 100 else abstract.replace('\n', ' ')
                print(f"   └── Found abstract ({len(abstract)} chars): {preview}")
            else:
                print("   └── Abstract not found")

            if (index + 1) % 20 == 0:
                df.to_csv(OUTPUT_FILE, index=False)
                print(f"   [Progress saved to {OUTPUT_FILE}]")
            
            # Sleep for a random interval between 2 and 5 seconds to be polite and avoid blocking
            time.sleep(random.uniform(2.0, 5.0))
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Saving progress...")
    except RateLimitException:
        print("\n[!] Rate limit reached (429). Saving progress and stopping...")
    except Exception as e:
        print(f"\n[!] Error: {e}. Saving progress...")
    finally:
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nDone! All data saved to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
