import ollama
import numpy as np

reviews = ["This is a great product", "Awesome!", "Worked very nicely",
            "Did not work", "Waste of money", "Never buying again",
            "Nao abri mais veio bem embalado", "cool xD"]

positive_phrase = "This is a good product"
negative_phrase = "This is a bad product"

def ollama_get_embedding(text: str) -> np.ndarray:

    response = ollama.embed(model="embeddinggemma", input=text)
    raw_embedding = response.embeddings[0]
    embedding = np.array(raw_embedding, dtype=np.float64)
    
    norm = np.linalg.norm(embedding)
    if norm > 0: # I'm not sure every model responds normalized
        return embedding / norm
    return embedding

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    # Since vectors are normalized, dot product is the cosine similarity
    return float(np.dot(a, b))

if __name__ == "__main__":
    print(f"Calculating embeddings for targets: '{positive_phrase}' and '{negative_phrase}'...")
    pos_emb = ollama_get_embedding(positive_phrase)
    neg_emb = ollama_get_embedding(negative_phrase)

    print("\nClassifying reviews:")
    for review in reviews:
        rev_emb = ollama_get_embedding(review)
        sim_pos = cosine_similarity(rev_emb, pos_emb)
        sim_neg = cosine_similarity(rev_emb, neg_emb)
        
        winner = "positive" if sim_pos > sim_neg else "negative"
            
        print(f"[{winner.upper()}] (pos: {sim_pos:.4f}, neg: {sim_neg:.4f}) -> {review}")
