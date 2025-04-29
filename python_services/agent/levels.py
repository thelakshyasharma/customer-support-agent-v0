from .docs_search import search_docs

def handle_level1(message):
    doc_result = search_docs(message)
    if doc_result:
        return f"Here's what I found in our docs: {doc_result} 😊"
    else:
        return "I couldn't find an exact answer in our docs, but I'm here to help further!"

def handle_level2(message):
    # Stub: In real use, ask diagnostic questions
    return "Let's troubleshoot this together! Can you tell me more about the issue? 🛠️" 