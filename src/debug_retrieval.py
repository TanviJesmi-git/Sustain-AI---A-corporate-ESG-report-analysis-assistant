from retrieve import retrieve

chunks = retrieve("water efficiency per employee target 200 liters", n_results=5, where={"company": "WIPRO"})
for c in chunks:
    if c["page_number"] == 29:
        print(c["content"])