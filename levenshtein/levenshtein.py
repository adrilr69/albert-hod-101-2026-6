import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
import random
import string

# algo for distance
def lev(s, t):
    n, m = len(s), len(t)
    
    # swap to make t shorter
    if n < m:
        s, t = t, s
        n, m = m, n

    curr = list(range(m + 1))
    
    for i in range(1, n + 1):
        prev = curr
        curr = [i] + [0] * m
        
        for j in range(1, m + 1):
            del_c = prev[j] + 1
            ins_c = curr[j - 1] + 1
            sub_c = prev[j - 1]
            
            if s[i - 1] != t[j - 1]:
                sub_c += 1
            
            curr[j] = min(del_c, ins_c, sub_c)
    
    return curr[m]

# --- csv part ---
print("doing csv stuff...")
df = pd.read_csv(r'C:\information_retrieval\levenshtein_pairs.csv', names=['s', 't'])

# run calc
df['dist'] = df.apply(lambda r: lev(str(r['s']), str(r['t'])), axis=1)

print("results:")
print(df)

df.to_csv(r'C:\information_retrieval\levenshtein_pairs_results.csv', index=False)

# --- complexity check ---
print("\nchecking speed...")
lens = [100, 500, 1000, 2000]
times = []
prods = []

for l in lens:
    s = ''.join(random.choices(string.ascii_lowercase, k=l))
    t = ''.join(random.choices(string.ascii_lowercase, k=l))
    
    t0 = time.time()
    x = lev(s, t)
    t1 = time.time()
    
    diff = t1 - t0
    p = l * l
    
    times.append(diff)
    prods.append(p)
    print(f"len {l}: {diff:.4f}s")

# --- plotting ---
print("\nmaking graph...")
plt.figure(figsize=(10, 6))

plt.scatter(prods, times, color='blue', label='data')

# regression line
z = np.polyfit(prods, times, 1)
p = np.poly1d(z)

plt.plot(prods, p(prods), color='red', label='fit')

plt.xlabel('n * m')
plt.ylabel('time (s)')
plt.title('Levenshtein Complexity')
plt.legend()

plt.savefig(r'C:\information_retrieval\levenshtein_complexity.png')
print("graph saved.")
print(f"slope: {z[0]}")
print("finished assignment 1.")
