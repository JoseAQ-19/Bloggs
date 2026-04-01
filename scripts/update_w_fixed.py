import glob
import os

for wf in glob.glob('.github/workflows/writer-*.yml'):
    with open(wf, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We are replacing EXACT STRING using concatenation to avoid PS interpolation
    gemini = 'GEMINI_API_KEY: $' + chr(123) + chr(123) + ' secrets.GEMINI_API_KEY ' + chr(125) + chr(125)
    models = 'MODELS_TOKEN_CEU: $' + chr(123) + chr(123) + ' secrets.MODELS_TOKEN_CEU ' + chr(125) + chr(125)
    token = 'TOKEN_MODELS: $' + chr(123) + chr(123) + ' secrets.TOKEN_MODELS ' + chr(125) + chr(125)
    
    if models not in content:
        replacement = gemini + '\n          ' + models + '\n          ' + token
        content = content.replace(gemini, replacement)
        
        with open(wf, 'w', encoding='utf-8', newline='') as fw:
            fw.write(content)
        print('Updated', wf)
