import glob

def do_it():
    for wf in glob.glob('.github/workflows/writer-*.yml'):
        with open(wf, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        out = []
        for line in lines:
            out.append(line)
            if 'GEMINI_API_KEY:' in line and 'secrets' in line:
                if 'TOKEN_MODELS' not in ''.join(lines): # only inject if not there
                    out.append('          MODELS_TOKEN_CEU: ${{ secrets.MODELS_TOKEN_CEU }}\n')
                    out.append('          TOKEN_MODELS: ${{ secrets.TOKEN_MODELS }}\n')
                    print(f"Updated {wf}")
        
        with open(wf, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(out)

do_it()
