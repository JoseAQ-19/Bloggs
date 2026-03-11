import re

files = [
    r'c:\Users\usuario\Desktop\Bloggs\content\es\ia\saaspocalypse-sobreviviran-las-empresas-de-software-a-la-ia-los-datos-que-no-te-cuentan.md',
    r'c:\Users\usuario\Desktop\Bloggs\content\en\fitness\metformin-longevity-hack-or-hype-en.md',
    r'c:\Users\usuario\Desktop\Bloggs\content\en\youtube\mrbeast-controversy-business-impact-en.md',
    r'c:\Users\usuario\Desktop\Bloggs\content\en\ia\anthropic-claude-3-5-sonnet-cost-savings-myth-en.md',
    r'c:\Users\usuario\Desktop\Bloggs\content\es\ia\inteligencia-artificial-la-estafa-del-siglo-xxi.md'
]

link_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')

out_file = r'c:\Users\usuario\Desktop\Bloggs\check_links_result.md'

with open(out_file, 'w', encoding='utf-8') as out:
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                links = link_pattern.findall(content)
                name = f.split('\\')[-1]
                out.write(f"-- {name} --\n")
                out.write(f"   TOTAL ENLACES EXTERNOS SALIENTES: {len(links)}\n")
                for anchor, url in links:
                    out.write(f"   -> {url}\n")
        except Exception as e:
            out.write(f"Error {f}\n")

