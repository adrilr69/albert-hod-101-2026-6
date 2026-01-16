import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict

# clean text
def clean(t):
    return re.findall(r'\w+', str(t).lower())

# calc stats manually
def get_stats(y_true, y_pred):
    classes = sorted(list(set(y_true)))
    matrix = defaultdict(lambda: defaultdict(int))
    
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
    
    total = len(y_true)
    correct = sum(matrix[c][c] for c in classes)
    acc = correct / total
    
    res = []
    for c in classes:
        tp = matrix[c][c]
        fp = sum(matrix[o][c] for o in classes if o != c)
        fn = sum(matrix[c][o] for o in classes if o != c)
        
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
        
        res.append({'Class': c, 'Prec': p, 'Rec': r, 'F1': f1})
        
    return acc, pd.DataFrame(res)

class NB:
    def __init__(self):
        self.alpha = 1.0
        self.priors = {}
        self.cond_probs = defaultdict(lambda: defaultdict(float))
        self.vocab = set()
        self.classes = []

    def train(self, texts, labels):
        print("training...")
        n = len(texts)
        self.classes = list(set(labels))
        
        # priors
        counts = Counter(labels)
        for c in self.classes:
            self.priors[c] = np.log(counts[c] / n)
        
        # word counts
        wc = defaultdict(Counter)
        for t, l in zip(texts, labels):
            toks = clean(t)
            wc[l].update(toks)
            self.vocab.update(toks)
        
        # cond probs
        v_len = len(self.vocab)
        for c in self.classes:
            total = sum(wc[c].values())
            denom = total + self.alpha * v_len
            
            for w in self.vocab:
                cnt = wc[c][w]
                self.cond_probs[c][w] = np.log((cnt + self.alpha) / denom)
            
            # unknown word handling
            self.cond_probs[c]['__unk__'] = np.log(self.alpha / denom)

    def predict(self, text):
        toks = clean(text)
        scores = {}
        
        for c in self.classes:
            s = self.priors[c]
            for t in toks:
                if t in self.vocab:
                    s += self.cond_probs[c][t]
                else:
                    s += self.cond_probs[c]['__unk__']
            scores[c] = s
        
        return max(scores, key=scores.get)

# load data
print("loading...")
path = r'C:\information_retrieval\classification dataset - ground_truth.csv'
df = pd.read_csv(path, header=None)
df = df[[0, 1]] # text, label
df.columns = ['text', 'label']

# split
split = int(0.8 * len(df))
train_df = df.iloc[:split]
test_df = df.iloc[split:].copy()

print(f"train: {len(train_df)}, test: {len(test_df)}")

# run model
model = NB()
model.train(train_df['text'].tolist(), train_df['label'].tolist())

print("predicting...")
test_df['pred'] = test_df['text'].apply(model.predict)

# stats
acc, stats = get_stats(test_df['label'].tolist(), test_df['pred'].tolist())

print(f"Accuracy: {acc:.4f}")
print(stats)

stats.to_csv(r'C:\information_retrieval\naive_bayes_results.csv', index=False)
