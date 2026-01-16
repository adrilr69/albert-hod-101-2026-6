import pandas as pd
import numpy as np
import re
from collections import Counter

# clean the text
def get_tokens(text):
    return re.findall(r'\w+', str(text).lower())

# math stuff for similarity
def calc_sim(v1, v2):
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    
    if n1 == 0 or n2 == 0:
        return 0.0
    
    return np.dot(v1, v2) / (n1 * n2)

# load data
print("loading data...")
path = r'C:\information_retrieval\tf_idf.csv' # hope this path is right
df = pd.read_csv(path)
data = df.iloc[:, 0].tolist()

# remove nan values
data = [str(x) for x in data if pd.notna(x) and str(x).strip() != '']
print(f"loaded {len(data)} items")

# tokenize everything
all_tokens = [get_tokens(x) for x in data]

# vocab list
vocab = sorted(list(set(w for t in all_tokens for w in t)))
w2i = {w: i for i, w in enumerate(vocab)}
N = len(data)

# calc IDF
print("calculating idf...")
counts = Counter()
for t in all_tokens:
    counts.update(set(t))

idf = {w: np.log(N / (c + 1)) for w, c in counts.items()}

# helper to get vector
def make_vec(tokens):
    vec = np.zeros(len(vocab))
    tf = Counter(tokens)
    
    for w, c in tf.items():
        if w in w2i:
            vec[w2i[w]] = c * idf.get(w, 0)
    return vec

# make the big matrix
print("building matrix...")
matrix = np.array([make_vec(t) for t in all_tokens])

# search list from assignment
queries = [
    "panatalon noir",
    "balai essuie glaces avant",
    "fromage fondu kiri",
    "lentilles 265g",
    "croutons à l'ail tipiak",
    "mozarella bille 150g",
    "sac a bandouillere en nylon",
    "mais doux saint eloi",
    "croustibat findus",
    "pipe rigate carrefour"
]

res = []

print("searching...")
for q in queries:
    q_toks = get_tokens(q)
    q_vec = make_vec(q_toks)
    
    # compare with everything
    sims = [calc_sim(q_vec, d_vec) for d_vec in matrix]
    
    best = np.argmax(sims)
    score = sims[best]
    match = data[best]
    
    res.append({
        "query": q,
        "match": match,
        "score": score
    })
    
    print(f"found: {match[:20]}... ({score:.2f})")

# save output
out_df = pd.DataFrame(res)
out_df.to_csv(r'C:\information_retrieval\tfidf_results.csv', index=False)
