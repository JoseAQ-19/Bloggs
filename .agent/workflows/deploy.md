---
description: Cómo desplegar cambios manuales del código en Vercel
---

Este workflow describe cómo desplegar cambios manuales de código en Vercel utilizando el deploy hook específico.

IMPORTANT:
- Úsalo SOLO para cambios manuales en el código (mejoras, fixes, etc.).
- NO lo uses para la generación automática de artículos por el workflow de GitHub Actions, ya que Vercel se actualiza automáticamente con los commits. Usar el hook en ese caso provocaría un doble despliegue y errores.

# Pasos

1. Asegúrate de que todos los cambios estén commiteados y pusheados a la rama `main` en GitHub.
2. Ejecuta el siguiente comando para triggerar el deploy en Vercel:

```bash
curl -X POST https://api.vercel.com/v1/integrations/deploy/prj_LjlrJDxuqvOkEGHe0Co0lUtbRWLe/52jxi0PIPf
```

3. Verifica la respuesta. Debería indicar que el trabajo está PENDING o QUEUED.
