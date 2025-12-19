import pandas as pd
import re
from collections import Counter
import io

# --- CONFIGURATION ---
INPUT_FILE = "neurips_papers_2015_2025.csv"

# Standard English Stop Words
STOP_WORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", "cannot", "could", 
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few", "for", 
    "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", 
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", 
    "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", 
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
    "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", 
    "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", 
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", 
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", 
    "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", 
    "yourselves", "via"
])

# Add domain-specific stop words that are too common in NeurIPS titles to be informative
STOP_WORDS.update([
    "dataset", "data", "datas", "learn", "learning", "learnt", "learned",
    "algorithm", "algorithms", "proposed", "propose", "proposal",
    "base", "based", "basis", "object", "objects", "method", "methods",
    "train", "training", "trained", "set", "sets", "recent", "recently",
    "paper", "papers", "result", "results", "model", "models",
    "neural", "network", "networks", "deep",
    "use", "using", "used", "usage",
    "problem", "problems",
    "approach", "approaches",
    "task", "tasks",
    "performance", "performances",
    "state", "art",
    "work", "works",
    "present", "presents", "presented",
    "show", "shows", "shown",
    "study", "studies",
    "experiment", "experiments", "experimental",
    "analysis", "analyses", "analyze",
    "framework", "frameworks",
    "technique", "techniques",
    "application", "applications",
    "novel", "new",
    "general", "generalized",
    "improve", "improves", "improved", "improvement",
    "evaluate", "evaluation", "evaluated",
    "different", "various"
])


def preprocess_title(title):
    """
    1. Lowercase
    2. Keep hyphenated words intact
    3. Remove other non-alphanumeric characters
    4. Tokenize & remove stop words
    """
    if not isinstance(title, str):
        return []

    # 1. Lowercase
    title = title.lower()

    # 2. Remove non-alphanumeric chars EXCEPT hyphens
    #    This keeps words like 'large-language-model' intact
    title = re.sub(r'[^a-z0-9\s-]', '', title)

    # 3. Split by whitespace
    words = title.split()

    # 4. Remove stop words
    words = [w for w in words if w not in STOP_WORDS]

    return words


def main():
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: The file '{INPUT_FILE}' was not found. Please run the scraper first.")
        return

    print(f"Loaded {len(df)} papers.")

    # Apply preprocessing
    df['keywords'] = df['Title'].apply(preprocess_title)

    # --- Analysis 1: Top 20 Keywords for the Entire 10 Years ---
    all_keywords_10y = [word for keywords in df['keywords'] for word in keywords]
    counter_10y = Counter(all_keywords_10y)
    top_20_10y = counter_10y.most_common(20)

    print("\n" + "="*40)
    print("TOP 20 KEYWORDS (Last 10 Years Aggregate)")
    print("="*40)
    for rank, (word, count) in enumerate(top_20_10y, 1):
        print(f"{rank}. {word}: {count}")

    # --- Analysis 2: Top 20 Keywords Per Year ---
    print("\n" + "="*40)
    print("TOP 20 KEYWORDS BY YEAR")
    print("="*40)
    
    years = sorted(df['Year'].unique(), reverse=True)

    for year in years:
        df_year = df[df['Year'] == year]
        all_keywords_year = [word for keywords in df_year['keywords'] for word in keywords]
        
        counter_year = Counter(all_keywords_year)
        top_20_year = counter_year.most_common(20)
        
        print(f"\n--- {year} (Papers: {len(df_year)}) ---")
        print(", ".join([f"{word} ({count})" for word, count in top_20_year]))

if __name__ == "__main__":
    main()