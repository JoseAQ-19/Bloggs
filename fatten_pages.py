import os
import frontmatter
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

STATIC_PAGES = {
    "content/about.md": """
    ACT AS: Corporate Communications Director.
    TASK: Write a comprehensive 'About Us' page for NovumWorld.
    LENGTH: 600 words.
    TONE: Professional, visionary, slightly rebellious but corporate safe.
    SECTIONS: Our Mission, The Team, Our Technology (mention AI transparency), Editorial Standards, Future Vision.
    """,
    "content/privacy.md": """
    ACT AS: GDPR Lawyer.
    TASK: Write a complete Privacy Policy for a tech blog.
    LENGTH: 800 words.
    SECTIONS: Data Collection, Cookies, User Rights, Third Party Vendors (AdSense), Contact for Privacy.
    TONE: Legal, precise, reassuring.
    """,
    "content/contact.md": """
    ACT AS: Customer Success Manager.
    TASK: Write a 'Contact Us' page.
    LENGTH: 400 words.
    CONTENT: Explain why we want feedback, list departments (Editorial, Business, Tech), Press Inquiries guidelines, Response time SLA.
    TONE: Welcoming but structured.
    """
}

def fatten_static_pages():
    print("🐘 ENGORDANDO PÁGINAS ESTÁTICAS (SEO BOOST)...")
    
    for filepath, prompt in STATIC_PAGES.items():
        if not os.path.exists(filepath): continue
        
        try:
            print(f"   ✍️ Reescribiendo: {filepath}...")
            post = frontmatter.load(filepath)
            
            resp = client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            
            post.content = resp.text.strip()
            
            with open(filepath, 'wb') as f:
                frontmatter.dump(post, f)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    fatten_static_pages()
