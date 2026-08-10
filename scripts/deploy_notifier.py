"""
deploy_notifier.py — Automatización de Sincronización Git y Deploy Hooks de Vercel
===================================================================================
Dispara la sincronización en tiempo real con GitHub y la activación instantánea de
producción en Vercel mediante Deploy Hooks cuando se generan nuevos artículos o cambios.
"""

import os
import subprocess
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Structured Logger
logger = logging.getLogger("deploy_notifier")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def trigger_vercel_deploy(hook_url: Optional[str] = None) -> bool:
    """
    Envía una petición HTTP POST al Deploy Hook de Vercel con reintentos y tolerancia a fallos.

    Args:
        hook_url: URL opcional del Deploy Hook. Si no se pasa, lee VERCEL_DEPLOY_HOOK_URL de env.

    Returns:
        bool: True si el hook respondió con éxito (HTTP 2xx), False en caso contrario.
    """
    url = hook_url or os.getenv("VERCEL_DEPLOY_HOOK_URL")

    if not url:
        logger.warning("[DEPLOY] VERCEL_DEPLOY_HOOK_URL no está configurada en las variables de entorno. Omitiendo disparo de Vercel.")
        return False

    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"[DEPLOY] Disparando Vercel Deploy Hook (intento {attempt}/{max_attempts})...")
            response = requests.post(
                url,
                json={"event": "auto_deploy", "source": "novum_autoblogger"},
                headers={"User-Agent": "NovumWorld-AutoDeploy/1.0"},
                timeout=15
            )

            if response.status_code in (200, 201, 202, 204):
                logger.info(f"[SUCCESS] Vercel Deploy Hook activado con éxito (HTTP {response.status_code}).")
                print(f"🚀 [SUCCESS] Vercel Deploy Hook activado (HTTP {response.status_code})")
                return True
            else:
                logger.warning(f"[DEPLOY] Vercel Deploy Hook devolvió status no esperado {response.status_code}: {response.text[:200]}")
                if attempt < max_attempts:
                    import time
                    time.sleep(2 * attempt)
        except requests.exceptions.RequestException as e:
            logger.warning(f"[DEPLOY] Error en petición HTTP al Deploy Hook (intento {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                import time
                time.sleep(2 * attempt)
        except Exception as e:
            logger.error(f"[DEPLOY] Error inesperado llamando a Vercel Deploy Hook: {e}")
            return False

    logger.warning("[DEPLOY] No se pudo activar el Deploy Hook de Vercel tras agotar los reintentos.")
    return False


def git_commit_and_push(
    commit_message: str = "feat(content): nuevo artículo publicado [auto-deploy]",
    cwd: Optional[str] = None
) -> bool:
    """
    Verifica cambios locales, ejecuta git add, commit, pull rebase y push de forma segura.

    Args:
        commit_message: Mensaje estructurado para el commit de Git.
        cwd: Directorio raíz de trabajo (por defecto raíz del repo).

    Returns:
        bool: True si se ejecutó o no había cambios pendientes, False si ocurrió algún error crítico.
    """
    work_dir = cwd or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        # 1. Comprobar si estamos en un repositorio Git
        check_repo = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if check_repo.returncode != 0:
            logger.warning("[GIT] No se detectó repositorio Git válido. Omitiendo commit & push.")
            return False

        # 2. Comprobar si hay cambios pendientes
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if status_proc.returncode != 0:
            logger.warning(f"[GIT] Error ejecutando git status: {status_proc.stderr}")
            return False

        uncommitted_changes = status_proc.stdout.strip()
        if not uncommitted_changes:
            logger.info("[GIT] No hay archivos modificados o creados pendientes de commit.")
            return True

        logger.info(f"[GIT] Cambios detectados ({len(uncommitted_changes.splitlines())} archivos). Ejecutando add & commit...")

        # 3. Git add .
        add_proc = subprocess.run(["git", "add", "."], cwd=work_dir, capture_output=True, text=True, check=False)
        if add_proc.returncode != 0:
            logger.warning(f"[GIT] Error en git add: {add_proc.stderr}")
            return False

        # 4. Git commit
        commit_proc = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if commit_proc.returncode != 0 and "nothing to commit" not in commit_proc.stdout.lower():
            logger.warning(f"[GIT] Error en git commit: {commit_proc.stderr}")
            return False

        logger.info(f"[GIT] Commit completado: '{commit_message}'")

        # 5. Git pull rebase & push (con tolerancia a concurrencia)
        pull_proc = subprocess.run(
            ["git", "pull", "--rebase", "--autostash"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if pull_proc.returncode != 0:
            logger.warning(f"[GIT] Advertencia en git pull --rebase: {pull_proc.stderr}")

        push_proc = subprocess.run(
            ["git", "push"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if push_proc.returncode != 0:
            logger.warning(f"[GIT] Advertencia en git push: {push_proc.stderr}")
            return False

        logger.info("[SUCCESS] Cambios sincronizados y subidos a GitHub con éxito.")
        return True

    except Exception as e:
        logger.warning(f"[GIT] Excepción durante la sincronización Git: {e}")
        return False


def trigger_production_deploy(
    commit_message: str = "feat(content): nuevo artículo publicado [auto-deploy]",
    run_git: bool = True,
    run_vercel: bool = True,
    hook_url: Optional[str] = None,
    cwd: Optional[str] = None
) -> Dict[str, bool]:
    """
    Función principal de orquestación de despliegue. Ejecuta sincronización Git y dispara Vercel Deploy Hook.
    Diseñada con patrón Fail-Safe: NUNCA lanza excepciones no capturadas al orquestador principal.

    Args:
        commit_message: Mensaje de commit para Git.
        run_git: Si True, ejecuta git commit & push.
        run_vercel: Si True, dispara el Deploy Hook de Vercel.
        hook_url: URL opcional del webhook de Vercel.
        cwd: Directorio raíz opcional para comandos git.

    Returns:
        dict: Resumen del estado {'git_synced': bool, 'vercel_triggered': bool}
    """
    result = {
        "git_synced": False,
        "vercel_triggered": False
    }

    try:
        if run_git:
            result["git_synced"] = git_commit_and_push(commit_message=commit_message, cwd=cwd)

        if run_vercel:
            result["vercel_triggered"] = trigger_vercel_deploy(hook_url=hook_url)

    except Exception as e:
        logger.error(f"[DEPLOY] Error inesperado en trigger_production_deploy: {e}")

    return result


if __name__ == "__main__":
    print("🚀 Ejecutando deploy_notifier en modo independiente...")
    res = trigger_production_deploy()
    print(f"Resultado: {res}")
