import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from src.agent import JavaDocAgent
from src.config import (AppConfig, EmailConfig, GitConfig, LLMConfig,
                        TeamsConfig, load_config)
from src.notifier import Notifier

# --- Config Tests ---

def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
git:
  repo_url: "http://git"
  token: "secret"
  base_branch: "PROD"
llm:
  api_key: "llm_secret"
email:
  enabled: true
  host: "smtp"
  port: 25
  user: "u"
  password: "p"
  recipients: ["a@b.com"]
teams:
  enabled: false
  webhook_url: "http://webhook"
""")
    config = load_config(str(config_file))
    assert config.git.base_branch == "PROD"
    assert config.email.enabled is True
    assert config.teams.enabled is False
    assert config.llm.api_key.get_secret_value() == "llm_secret"

def test_load_config_env_override(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
git:
  repo_url: "http://git"
  token: "placeholder"
  base_branch: "PROD"
llm:
  api_key: "placeholder"
email:
  enabled: false
  host: "smtp"
  port: 25
  user: "u"
  password: "p"
  recipients: []
teams:
  enabled: false
  webhook_url: "url"
""")
    monkeypatch.setenv("GIT_TOKEN", "env_token")
    monkeypatch.setenv("GEMINI_API_KEY", "env_api_key")
    
    config = load_config(str(config_file))
    assert config.git.token.get_secret_value() == "env_token"
    assert config.llm.api_key.get_secret_value() == "env_api_key"

def test_load_config_base_url(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
git:
  repo_url: "http://git"
  token: "t"
  base_branch: "PROD"
llm:
  api_key: "k"
  model_name: "custom"
  base_url: "http://local:1234/v1"
email:
  enabled: false
  host: "h"
  port: 25
  user: "u"
  password: "p"
  recipients: []
teams:
  enabled: false
  webhook_url: "w"
""")
    config = load_config(str(config_file))
    assert config.llm.base_url == "http://local:1234/v1"


# --- Notifier Tests ---

@pytest.fixture
def mock_email_config():
    return EmailConfig(
        enabled=True, host="smtp", port=587, user="me", 
        password=SecretStr("pass"), recipients=["you"]
    )

@pytest.fixture
def mock_teams_config():
    return TeamsConfig(enabled=True, webhook_url=SecretStr("http://hook"))

def test_send_email(mock_email_config, mock_teams_config):
    notifier = Notifier(mock_email_config, mock_teams_config)
    
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        notifier.send_email("Subject", "Body")
        
        mock_smtp.assert_called_with("smtp", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_with("me", "pass")
        mock_server.send_message.assert_called_once()

def test_send_teams(mock_email_config, mock_teams_config):
    notifier = Notifier(mock_email_config, mock_teams_config)
    
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        notifier.send_teams_notification("Title", "Msg")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://hook"
        assert "Javadoc Automation Bot" in kwargs['data']

# --- Agent Tests ---

def test_agent_generation():
    llm_config = LLMConfig(api_key=SecretStr("key"), model_name="dummy")
    
    # Mock the Agent class inside src.agent
    with patch("src.agent.Agent") as MockAgent:
        mock_agent_instance = MagicMock()
        MockAgent.return_value = mock_agent_instance
        
        mock_result = MagicMock()
        mock_result.data = "/** Doc */ public class A {}"
        mock_agent_instance.run_sync.return_value = mock_result
        
        agent = JavaDocAgent(llm_config)
        result = agent.generate_javadoc("public class A {}")
        
        assert result == "/** Doc */ public class A {}"
        mock_agent_instance.run_sync.assert_called_with("public class A {}")
