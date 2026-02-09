# NovumWorld Blog

## Despliegue en Vercel

Para desplegar cambios manuales en el código (mejoras, correcciones, etc.) en Vercel, se debe utilizar el siguiente Deploy Hook **después de hacer push a GitHub**:

[Deploy Hook](https://api.vercel.com/v1/integrations/deploy/prj_LjlrJDxuqvOkEGHe0Co0lUtbRWLe/52jxi0PIPf)

**Importante:**
- Este hook es **SOLO** para cambios manuales en el código.
- **NO** debe usarse cuando el workflow de GitHub Actions genera artículos automáticamente. En ese caso, Vercel detecta el commit automáticamente. Usar el hook provocaría un despliegue doble y posibles errores.

Para ejecutar el despliegue manualmente desde la terminal:

```bash
curl -X POST https://api.vercel.com/v1/integrations/deploy/prj_LjlrJDxuqvOkEGHe0Co0lUtbRWLe/52jxi0PIPf
```
