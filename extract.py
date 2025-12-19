import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin

# --- CONFIGURATION ---
BASE_URL = "https://dblp.org/db/conf/nips/index.html"
ROOT_URL = "https://dblp.org/"
OUTPUT_FILE = "neurips_papers_2015_2025.csv"

# Time range settings
START_YEAR = 2015
END_YEAR = 2025

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "From": "researcher@example.com"
}

def get_soup(url):
    """Helper to fetch a URL and return a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_years_links(soup):
    """
    Parses the main index page to find links to specific conference years.
    Handles both 'nipsYYYY' and 'neuripsYYYY' file naming conventions.
    """
    valid_links = []
    
    # Find all links on the main DBLP NIPS page
    all_links = soup.find_all('a', href=True)
    
    print(f"Scanning {len(all_links)} links from main index...")
    
    for link in all_links:
        href = link['href']
        
        # --- CRITICAL FIX ---
        # Matches: "conf/nips/nips2019.html" OR "conf/nips/neurips2024.html"
        # The (?: ... ) group is a non-capturing group for the prefix variants.
        match = re.search(r'conf/nips/(?:nips|neurips)(\d{4})\.html', href)
        
        if match:
            year = int(match.group(1))
            
            # Filter by requested year range
            if START_YEAR <= year <= END_YEAR:
                full_url = urljoin(ROOT_URL, href)
                # Avoid duplicates
                if (year, full_url) not in valid_links:
                    valid_links.append((year, full_url))
    
    # Sort by year descending (Newest first)
    return sorted(list(set(valid_links)), key=lambda x: x[0], reverse=True)

def parse_conference_page(year, url):
    """
    Visits a specific year's page and extracts paper details.
    """
    print(f"--> Scraping Year: {year} from {url}...")
    soup = get_soup(url)
    if not soup:
        return []

    papers = []
    
    # DBLP structure: Papers are listed as 'li' items with class 'entry inproceedings'
    entries = soup.find_all('li', class_='entry inproceedings')
    
    print(f"    Found {len(entries)} papers. Extracting details...")

    for entry in entries:
        try:
            # 1. Extract Title
            title_span = entry.find('span', class_='title')
            title = title_span.get_text(strip=True) if title_span else "Unknown Title"
            
            # 2. Extract Authors
            author_spans = entry.find_all('span', itemprop='author')
            authors = [a.get_text(strip=True) for a in author_spans]
            authors_str = ", ".join(authors)
            
            # 3. Extract External Link (usually points to the PDF/Abstract)
            link_tag = entry.find('li', class_='ee')
            if link_tag and link_tag.find('a'):
                paper_link = link_tag.find('a')['href']
            else:
                paper_link = "N/A"

            papers.append({
                'Year': year,
                'Title': title,
                'Authors': authors_str,
                'Link': paper_link
            })
            
        except Exception as e:
            # Silent continue on minor errors to keep the loop running
            continue
            
    return papers

def main():
    print(f"Starting Scraper for DBLP NeurIPS ({START_YEAR} - {END_YEAR})...")
    
    # 1. Get the Main Index
    index_soup = get_soup(BASE_URL)
    if not index_soup:
        print("Failed to load main index. Check your connection.")
        return

    # 2. Get links for the relevant years (using the fixed Regex)
    year_links = extract_years_links(index_soup)
    
    if not year_links:
        print(f"No conference links found for the range {START_YEAR}-{END_YEAR}. Check the Regex or URL.")
        return

    print(f"Years found: {[y[0] for y in year_links]}")

    print(year_links)
    
    # all_data = []

    # 3. Loop through each year
    # for year, link in year_links:
    #     year_data = parse_conference_page(year, link)
    #     all_data.extend(year_data)
        
    #     # POLITE WAIT: Sleep 2 seconds between requests
    #     time.sleep(2) 

    # # 4. Save to CSV
    # if all_data:
    #     keys = all_data[0].keys()
    #     with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    #         dict_writer = csv.DictWriter(f, fieldnames=keys)
    #         dict_writer.writeheader()
    #         dict_writer.writerows(all_data)
    #     print(f"\nSuccess! Scraped {len(all_data)} papers.")
    #     print(f"Data saved to: {OUTPUT_FILE}")
    # else:
    #     print("No data found.")

if __name__ == "__main__":
    main()
