#!/bin/bash
# ============================================
# 🔄 RENOVAR COOKIES DE NOTEBOOKLM
# Ejecutar cuando el workflow falle por auth
# Uso: ./refresh_auth.sh
# ============================================

echo "🔄 RENOVANDO COOKIES DE NOTEBOOKLM..."
echo "======================================="
echo ""

# 1. Re-autenticar (abre Chrome, haces login si es necesario)
echo "📝 Paso 1: Abriendo autenticación..."
echo "   → Si se abre Chrome, inicia sesión con tu cuenta Google."
echo "   → Si ya tienes sesión, se cerrará solo."
echo ""

notebooklm-mcp-auth

# 2. Verificar que se generó el archivo
AUTH_FILE="$HOME/.notebooklm-mcp/auth.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "❌ ERROR: No se generó auth.json"
    echo "   Intenta ejecutar manualmente: notebooklm-mcp-auth"
    exit 1
fi

echo ""
echo "✅ Paso 1 completado: auth.json actualizado"
echo ""

# 3. Copiar al portapapeles
cat "$AUTH_FILE" | pbcopy
echo "📋 Paso 2: Contenido copiado al portapapeles (⌘+V para pegar)"
echo ""

# 4. Instrucciones para GitHub
echo "======================================="
echo "🚀 AHORA HAZ ESTO (30 segundos):"
echo "======================================="
echo ""
echo "1. Abre: https://github.com/JoseAQ-19/Bloggs/settings/secrets/actions"
echo "2. Busca el secreto 'NOTEBOOKLM_AUTH'"
echo "3. Clic en el lápiz (editar) ✏️"
echo "4. Borra el contenido viejo"
echo "5. Pega (⌘+V) el nuevo contenido"
echo "6. Clic en 'Update secret'"
echo ""
echo "✅ ¡LISTO! Las próximas ejecuciones usarán las cookies nuevas."
echo ""

# 5. Mostrar fecha de expiración estimada
EXTRACTED=$(python3 -c "
import json
from datetime import datetime, timedelta
with open('$AUTH_FILE') as f:
    data = json.load(f)
ts = data.get('extracted_at', 0)
dt = datetime.fromtimestamp(ts)
exp = dt + timedelta(weeks=3)
print(f'Extraídas: {dt.strftime(\"%d/%m/%Y %H:%M\")}')
print(f'Caducan aprox: {exp.strftime(\"%d/%m/%Y\")} (en ~3 semanas)')
" 2>/dev/null)

if [ -n "$EXTRACTED" ]; then
    echo "📅 $EXTRACTED"
fi
