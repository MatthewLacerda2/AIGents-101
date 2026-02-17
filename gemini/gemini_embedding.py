import numpy as np
from gemini_client import get_gemini_embeddings

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

reviews = ["This is a great product", "Awesome!", "Worked very nicely",
            "Did not work", "Waste of money", "Never buying again",
            "Nao abri mais veio bem embalado", "cool xD"]

positive_phrase = "This is good"
negative_phrase = "This is bad"

def classify_reviews():
    # Pre-calculate target embeddings
    print(f"Calculating embeddings for targets: '{positive_phrase}' and '{negative_phrase}'...")
    pos_emb = get_gemini_embeddings(positive_phrase)
    neg_emb = get_gemini_embeddings(negative_phrase)

    print("\nClassifying reviews:")
    for review in reviews:
        rev_emb = get_gemini_embeddings(review)
        sim_pos = cosine_similarity(rev_emb, pos_emb)
        sim_neg = cosine_similarity(rev_emb, neg_emb)
        
        winner = "positive" if sim_pos > sim_neg else "negative"
            
        print(f"[{winner.upper()}] (pos: {sim_pos:.4f}, neg: {sim_neg:.4f}) -> {review}")

if __name__ == "__main__":
    classify_reviews()
