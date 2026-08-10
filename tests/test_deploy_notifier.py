"""
test_deploy_notifier.py — Tests para el módulo de despliegue automatizado
=========================================================================
Verifica la lógica de trigger_production_deploy(), trigger_vercel_deploy(),
y git_commit_and_push() usando mocks para simular respuestas HTTP y comandos git.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, call
from deploy_notifier import (
    trigger_vercel_deploy,
    git_commit_and_push,
    trigger_production_deploy,
)


# ═══════════════════════════════════════════════════════════════════
# Tests: trigger_vercel_deploy()
# ═══════════════════════════════════════════════════════════════════

class TestTriggerVercelDeploy:
    """Tests for the Vercel Deploy Hook HTTP trigger."""

    @patch("deploy_notifier.requests.post")
    def test_successful_deploy_hook_200(self, mock_post):
        """HTTP 200 response should return True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = trigger_vercel_deploy(hook_url="https://api.vercel.com/v1/deploy/test")
        assert result is True
        mock_post.assert_called_once()

    @patch("deploy_notifier.requests.post")
    def test_successful_deploy_hook_201(self, mock_post):
        """HTTP 201 response should return True."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = trigger_vercel_deploy(hook_url="https://api.vercel.com/v1/deploy/test")
        assert result is True

    @patch("deploy_notifier.requests.post")
    def test_failed_deploy_hook_500(self, mock_post):
        """HTTP 500 response should exhaust retries and return False."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        result = trigger_vercel_deploy(hook_url="https://api.vercel.com/v1/deploy/test")
        assert result is False
        assert mock_post.call_count == 3  # 3 retry attempts

    def test_no_url_configured_returns_false(self):
        """Missing VERCEL_DEPLOY_HOOK_URL should return False without crashing."""
        with patch.dict(os.environ, {}, clear=True):
            result = trigger_vercel_deploy(hook_url=None)
            assert result is False

    @patch("deploy_notifier.requests.post")
    def test_network_exception_returns_false(self, mock_post):
        """Network errors should be caught and return False."""
        import requests as req
        mock_post.side_effect = req.exceptions.ConnectionError("Connection refused")

        result = trigger_vercel_deploy(hook_url="https://api.vercel.com/v1/deploy/test")
        assert result is False
        assert mock_post.call_count == 3  # Retried 3 times

    @patch("deploy_notifier.requests.post")
    def test_sends_correct_payload(self, mock_post):
        """Verify the POST request includes the expected JSON body and headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        trigger_vercel_deploy(hook_url="https://api.vercel.com/v1/deploy/test")

        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["source"] == "novum_autoblogger"
        assert "User-Agent" in call_kwargs.kwargs["headers"]
        assert call_kwargs.kwargs["timeout"] == 15

    @patch("deploy_notifier.requests.post")
    def test_reads_url_from_env(self, mock_post):
        """When no url arg is passed, should read from VERCEL_DEPLOY_HOOK_URL env."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        env_url = "https://api.vercel.com/v1/deploy/from-env"
        with patch.dict(os.environ, {"VERCEL_DEPLOY_HOOK_URL": env_url}):
            result = trigger_vercel_deploy()
            assert result is True
            assert mock_post.call_args.args[0] == env_url


# ═══════════════════════════════════════════════════════════════════
# Tests: git_commit_and_push()
# ═══════════════════════════════════════════════════════════════════

class TestGitCommitAndPush:
    """Tests for the Git synchronization logic."""

    @patch("deploy_notifier.subprocess.run")
    def test_no_changes_returns_true(self, mock_run):
        """When git status shows no changes, should return True without committing."""
        # git rev-parse succeeds
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),    # rev-parse
            MagicMock(returncode=0, stdout=""),          # git status (empty = no changes)
        ]

        result = git_commit_and_push(cwd="/tmp")
        assert result is True
        assert mock_run.call_count == 2  # Only rev-parse + status

    @patch("deploy_notifier.subprocess.run")
    def test_not_a_git_repo_returns_false(self, mock_run):
        """When not inside a git repo, should return False gracefully."""
        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal: not a git repository")

        result = git_commit_and_push(cwd="/tmp")
        assert result is False

    @patch("deploy_notifier.subprocess.run")
    def test_full_commit_push_cycle(self, mock_run):
        """When changes exist, should run add, commit, pull rebase, and push."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),                  # rev-parse
            MagicMock(returncode=0, stdout=" M content/test.md\n"),  # git status
            MagicMock(returncode=0),                                  # git add
            MagicMock(returncode=0, stdout="1 file changed"),        # git commit
            MagicMock(returncode=0),                                  # git pull --rebase
            MagicMock(returncode=0),                                  # git push
        ]

        result = git_commit_and_push(commit_message="test commit", cwd="/tmp")
        assert result is True
        assert mock_run.call_count == 6

    @patch("deploy_notifier.subprocess.run")
    def test_push_failure_returns_false(self, mock_run):
        """When git push fails, should return False."""
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="true"),
            MagicMock(returncode=0, stdout=" M content/test.md\n"),
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout="1 file changed"),
            MagicMock(returncode=0),
            MagicMock(returncode=1, stderr="rejected"),  # push fails
        ]

        result = git_commit_and_push(cwd="/tmp")
        assert result is False


# ═══════════════════════════════════════════════════════════════════
# Tests: trigger_production_deploy() (orchestration)
# ═══════════════════════════════════════════════════════════════════

class TestTriggerProductionDeploy:
    """Tests for the top-level orchestration function."""

    @patch("deploy_notifier.trigger_vercel_deploy")
    @patch("deploy_notifier.git_commit_and_push")
    def test_both_steps_succeed(self, mock_git, mock_vercel):
        """When both git and vercel succeed, result dict should reflect True/True."""
        mock_git.return_value = True
        mock_vercel.return_value = True

        result = trigger_production_deploy(run_git=True, run_vercel=True)
        assert result["git_synced"] is True
        assert result["vercel_triggered"] is True

    @patch("deploy_notifier.trigger_vercel_deploy")
    @patch("deploy_notifier.git_commit_and_push")
    def test_skip_git_in_ci(self, mock_git, mock_vercel):
        """When run_git=False (CI mode), git should not be called."""
        mock_vercel.return_value = True

        result = trigger_production_deploy(run_git=False, run_vercel=True)
        mock_git.assert_not_called()
        assert result["git_synced"] is False
        assert result["vercel_triggered"] is True

    @patch("deploy_notifier.trigger_vercel_deploy")
    @patch("deploy_notifier.git_commit_and_push")
    def test_vercel_failure_does_not_crash(self, mock_git, mock_vercel):
        """Vercel failure should not raise — fail-safe pattern."""
        mock_git.return_value = True
        mock_vercel.return_value = False

        result = trigger_production_deploy()
        assert result["git_synced"] is True
        assert result["vercel_triggered"] is False

    @patch("deploy_notifier.trigger_vercel_deploy")
    @patch("deploy_notifier.git_commit_and_push")
    def test_exception_does_not_crash(self, mock_git, mock_vercel):
        """Any unhandled exception should be caught — never crashes the orchestrator."""
        mock_git.side_effect = RuntimeError("unexpected error")

        result = trigger_production_deploy()
        # Should not raise, just return partial result
        assert isinstance(result, dict)
        assert result["git_synced"] is False
