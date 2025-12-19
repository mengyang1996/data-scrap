import pandas as pd 
import re
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from analysis import STOP_WORDS


df = pd.read_csv("datasets/neurips_papers_with_abstracts.csv")

print(f"Loaded {len(df)} papers from the CSV file.")
# Print the first 5 rows of the DataFrame
print(df.head())

# Identify columns (handling potential case differences)
title_col = 'title' if 'title' in df.columns else 'Title'
year_col = 'year' if 'year' in df.columns else 'Year'
abstract_col = 'abstract' if 'abstract' in df.columns else ('Abstract' if 'Abstract' in df.columns else None)

print(title_col, year_col, abstract_col)

# Initialize stemmer
stemmer = PorterStemmer()

STOP_WORDS_STEMMED = set(stemmer.stem(w) for w in STOP_WORDS)

def tokenize_stem(text):
    tokens = re.findall(r'\b\w\w+\b', text.lower())
    stems = [stemmer.stem(token) for token in tokens]
    return [s for s in stems if s not in STOP_WORDS_STEMMED]

if title_col in df.columns and year_col in df.columns:
    print(f"\nAnalyzing topics based on '{title_col}' and {abstract_col if abstract_col else 'no'} abstracts for each '{year_col}' using LDA and CountVectorizer...")
    
    years = sorted(df[year_col].unique())
    
    for year in years:
        print(f"\n--- Year: {year} ---")
        df_year = df[df[year_col] == year]
        
        titles = df_year[title_col].fillna('').astype(str)
        if abstract_col:
            abstracts = df_year[abstract_col].fillna('').astype(str)
            documents = (titles + " " + abstracts).tolist()
        else:
            documents = titles.tolist()
        
        if len(documents) < 5:
            print("Not enough papers to analyze.")
            continue
            
        # Count Vectorization (Bag of Words)
        tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, tokenizer=tokenize_stem, token_pattern=None)
        try:
            tf = tf_vectorizer.fit_transform(documents)
        except ValueError:
            print("Vocabulary is empty or insufficient data.")
            continue

        # LDA Analysis
        lda = LatentDirichletAllocation(n_components=20, max_iter=100, learning_method='online', random_state=42)
        lda.fit(tf)
        
        feature_names = tf_vectorizer.get_feature_names_out()
        for topic_idx, topic in enumerate(lda.components_):
            top_features_ind = topic.argsort()[:-21:-1]
            top_features = [feature_names[i] for i in top_features_ind]
            print(f"Topic #{topic_idx + 1}: {', '.join(top_features)}")
else:
    print(f"Could not find '{title_col}' or '{year_col}' columns.")