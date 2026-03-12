import os
import glob

def get_latest_26():
    md_files = glob.glob(os.path.join("content", "**", "*.md"), recursive=True)
    md_files = [f for f in md_files if not os.path.basename(f).startswith("_index")]
    
    # Sort by modification time
    md_files.sort(key=os.path.getmtime, reverse=True)
    
    latest_26 = md_files[:26]
    for i, path in enumerate(latest_26):
        print(f"{i+1}. {path}")

if __name__ == "__main__":
    get_latest_26()
