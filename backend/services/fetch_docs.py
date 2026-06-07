import httpx
from bs4 import BeautifulSoup
import os

def fetch_manim_reference():
    url = "https://docs.manim.community/en/stable/reference.html"
    print(f"Fetching latest Manim docs from {url}...")
    
    try:
        response = httpx.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get class names and short descriptions from the table of contents
        classes = []
        for item in soup.select('a.reference.internal'):
            text = item.get_text(strip=True)
            if text and not text.startswith("manim."):
                classes.append(text)
        
        doc_content = "\n".join(list(set(classes))[:150]) # Use the first 150 unique entries
        
        output_path = os.path.join("backend", "services", "manim_docs.txt")
        with open(output_path, "w") as f:
            f.write(doc_content)
            
        print(f"Successfully saved {len(classes)} reference entries to {output_path}")
        return doc_content
    except Exception as e:
        print(f"Failed to fetch docs: {e}")
        return ""

if __name__ == "__main__":
    fetch_manim_reference()
