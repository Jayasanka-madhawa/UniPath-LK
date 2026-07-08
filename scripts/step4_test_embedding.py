import ollama

EMBED_MODEL = "nomic-embed-text"

text = "Students who sat the A/L exam more than three times are ineligible."

response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
vector = response["embedding"]

print("Ollama embedding works!")
print("Model:", EMBED_MODEL)
print("Vector length:", len(vector))
print("First 5 numbers:", vector[:5])