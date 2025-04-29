import os

def search_docs(query):
    doc_path = os.path.join(os.path.dirname(__file__), '../../docs/faq.md')
    if not os.path.exists(doc_path):
        return None
    query_words = set(query.lower().split())
    with open(doc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if any(word in line.lower() for word in query_words):
            # Return the line and the next line for context
            snippet = line.strip()
            if i + 1 < len(lines):
                snippet += ' ' + lines[i+1].strip()
            return snippet
    return None 