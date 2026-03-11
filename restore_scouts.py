import glob

files = glob.glob(r"c:\Users\usuario\Desktop\Bloggs\.github\workflows\scout-*.yml")
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Revert back to using OPENROUTER_SCOUT_KEY for scout workflows
    nuevo = content.replace('OPENROUTER_SCOUT_KEY: ${{ secrets.OPEN_ROUTER_API_KEY }}', 'OPENROUTER_SCOUT_KEY: ${{ secrets.OPENROUTER_SCOUT_KEY }}')
    
    if nuevo != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(nuevo)
        print(f"Fixed {f}")
