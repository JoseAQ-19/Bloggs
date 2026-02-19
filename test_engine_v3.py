from scripts.content_engine_pro import main_upgrade_engine

# Lista de Candidatos a Regeneración Quirúrgica
TARGETS = [
    '/Users/manolo/Bloggs/content/en/ia/el-ano-en-que-la-realidad-virtual-derroto-al-mund.md',
    '/Users/manolo/Bloggs/content/en/ia/la-elites-digitales-amos-del-mundo-o-nuevos-parasi.md',
    '/Users/manolo/Bloggs/content/en/viral/decoding-viral-vortex-ai-analog-unexpected-nuptials-en.md'  # El del tono raro
]

print('�� INICIANDO PRUEBA DE FUEGO CONTENT ENGINE V3...')
for target in TARGETS:
    main_upgrade_engine(target)

print('✅ PRUEBA FINALIZADA.')
