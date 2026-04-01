import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import AccountConfig, AppConfig, ProviderConfig, load_accounts_config


class TestProviderConfig:
	def test_default_values(self):
		config = ProviderConfig(name='test', domain='https://example.com')
		assert config.name == 'test'
		assert config.domain == 'https://example.com'
		assert config.login_path == '/login'
		assert config.sign_in_path == '/api/user/sign_in'
		assert config.user_info_path == '/api/user/self'
		assert config.api_user_key == 'new-api-user'
		assert config.bypass_method is None
		assert config.waf_cookie_names == []
		assert config.check_in_method == 'POST'

	def test_from_dict_basic(self):
		data = {'domain': 'https://example.com'}
		config = ProviderConfig.from_dict('myprovider', data)
		assert config.name == 'myprovider'
		assert config.domain == 'https://example.com'
		assert config.sign_in_path == '/api/user/sign_in'

	def test_from_dict_full(self):
		data = {
			'domain': 'https://example.com',
			'login_path': '/mylogin',
			'sign_in_path': '/api/checkin',
			'user_info_path': '/api/me',
			'api_user_key': 'x-user',
			'check_in_method': 'GET',
		}
		config = ProviderConfig.from_dict('myprovider', data)
		assert config.login_path == '/mylogin'
		assert config.sign_in_path == '/api/checkin'
		assert config.user_info_path == '/api/me'
		assert config.api_user_key == 'x-user'
		assert config.check_in_method == 'GET'

	def test_needs_waf_cookies_false(self):
		config = ProviderConfig(name='test', domain='https://example.com')
		assert not config.needs_waf_cookies()

	def test_needs_waf_cookies_true(self):
		config = ProviderConfig(
			name='test',
			domain='https://example.com',
			bypass_method='waf_cookies',
			waf_cookie_names=['acw_tc'],
		)
		assert config.needs_waf_cookies()

	def test_needs_manual_check_in_true(self):
		config = ProviderConfig(name='test', domain='https://example.com', sign_in_path='/api/sign_in')
		assert config.needs_manual_check_in()

	def test_needs_manual_check_in_false(self):
		config = ProviderConfig(name='test', domain='https://example.com', sign_in_path=None)
		assert not config.needs_manual_check_in()

	def test_waf_cookies_cleared_when_empty(self):
		config = ProviderConfig(
			name='test',
			domain='https://example.com',
			bypass_method='waf_cookies',
			waf_cookie_names=[],
		)
		assert config.bypass_method is None

	def test_waf_cookies_invalid_names_filtered(self):
		config = ProviderConfig(
			name='test',
			domain='https://example.com',
			bypass_method='waf_cookies',
			waf_cookie_names=['valid_cookie', '', '  '],
		)
		assert config.waf_cookie_names == ['valid_cookie']


class TestAppConfig:
	def test_load_from_env_default_providers(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		assert 'anyrouter' in config.providers
		assert 'callxyq' in config.providers
		assert 'fakerclaw' in config.providers
		assert 'gemai' in config.providers
		assert 'zhj' in config.providers
		assert 'nih' in config.providers
		assert 'neb' in config.providers
		assert 'test' in config.providers
		assert 'hetang' in config.providers

	def test_hetang_provider_configured(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		hetang = config.get_provider('hetang')
		assert hetang is not None
		assert hetang.name == 'hetang'
		assert hetang.domain == 'https://hetang.lyvideo.top'
		assert hetang.sign_in_path == '/api/user/checkin'
		assert hetang.user_info_path == '/api/user/self'
		assert hetang.api_user_key == 'new-api-user'
		assert not hetang.needs_waf_cookies()
		assert hetang.needs_manual_check_in()

	def test_get_provider_returns_none_for_unknown(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		assert config.get_provider('nonexistent') is None

	def test_get_provider_returns_config(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		provider = config.get_provider('hetang')
		assert isinstance(provider, ProviderConfig)

	def test_custom_providers_merged(self, monkeypatch):
		custom = json.dumps({'myprovider': {'domain': 'https://myprovider.example.com'}})
		monkeypatch.setenv('PROVIDERS', custom)
		config = AppConfig.load_from_env()
		assert 'myprovider' in config.providers
		assert 'hetang' in config.providers  # default providers still present

	def test_custom_provider_overrides_default(self, monkeypatch):
		custom = json.dumps({'hetang': {'domain': 'https://custom-hetang.example.com'}})
		monkeypatch.setenv('PROVIDERS', custom)
		config = AppConfig.load_from_env()
		hetang = config.get_provider('hetang')
		assert hetang.domain == 'https://custom-hetang.example.com'

	def test_invalid_providers_env_ignored(self, monkeypatch):
		monkeypatch.setenv('PROVIDERS', 'not-valid-json')
		config = AppConfig.load_from_env()
		# Should fall back to defaults
		assert 'hetang' in config.providers

	def test_providers_env_not_dict_ignored(self, monkeypatch):
		monkeypatch.setenv('PROVIDERS', '["not", "a", "dict"]')
		config = AppConfig.load_from_env()
		# Should fall back to defaults
		assert 'hetang' in config.providers

	def test_anyrouter_provider_configured(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		anyrouter = config.get_provider('anyrouter')
		assert anyrouter is not None
		assert anyrouter.domain == 'https://anyrouter.top'
		assert anyrouter.needs_waf_cookies()

	def test_agentrouter_provider_configured(self, monkeypatch):
		monkeypatch.delenv('PROVIDERS', raising=False)
		config = AppConfig.load_from_env()
		agentrouter = config.get_provider('agentrouter')
		assert agentrouter is not None
		assert agentrouter.domain == 'https://agentrouter.org'
		assert agentrouter.sign_in_path is None  # no manual sign-in needed
		assert agentrouter.needs_waf_cookies()


class TestAccountConfig:
	def test_from_dict_with_access_token(self):
		data = {
			'name': 'myaccount',
			'provider': 'hetang',
			'access_token': 'mytoken123',
			'api_user': 'user@example.com',
		}
		account = AccountConfig.from_dict(data, 0)
		assert account.name == 'myaccount'
		assert account.provider == 'hetang'
		assert account.access_token == 'mytoken123'
		assert account.api_user == 'user@example.com'

	def test_from_dict_defaults_to_anyrouter_provider(self):
		data = {
			'access_token': 'mytoken',
			'api_user': 'user@example.com',
		}
		account = AccountConfig.from_dict(data, 0)
		assert account.provider == 'anyrouter'

	def test_from_dict_auto_name(self):
		data = {'access_token': 'mytoken', 'api_user': 'user@example.com'}
		account = AccountConfig.from_dict(data, 2)
		assert account.name == 'Account 3'

	def test_has_access_token(self):
		account = AccountConfig(api_user='u', provider='hetang', access_token='tok')
		assert account.has_access_token()

	def test_has_no_access_token(self):
		account = AccountConfig(api_user='u', provider='hetang')
		assert not account.has_access_token()

	def test_has_credentials(self):
		account = AccountConfig(api_user='u', provider='hetang', username='user', password='pass')
		assert account.has_credentials()

	def test_has_no_credentials(self):
		account = AccountConfig(api_user='u', provider='hetang', username='user')
		assert not account.has_credentials()

	def test_has_cookies_dict(self):
		account = AccountConfig(api_user='u', provider='hetang', cookies={'session': 'abc'})
		assert account.has_cookies()

	def test_has_cookies_string(self):
		account = AccountConfig(api_user='u', provider='hetang', cookies='session=abc')
		assert account.has_cookies()

	def test_has_no_cookies(self):
		account = AccountConfig(api_user='u', provider='hetang', cookies={})
		assert not account.has_cookies()

	def test_get_display_name_with_name(self):
		account = AccountConfig(api_user='u', provider='hetang', name='hetang')
		assert account.get_display_name(0) == 'hetang'

	def test_get_display_name_without_name(self):
		account = AccountConfig(api_user='u', provider='hetang')
		assert account.get_display_name(3) == 'Account 4'


class TestLoadAccountsConfig:
	def test_missing_env_var(self, monkeypatch):
		monkeypatch.delenv('ANYROUTER_ACCOUNTS', raising=False)
		result = load_accounts_config()
		assert result is None

	def test_valid_access_token_config(self, monkeypatch):
		accounts = json.dumps(
			[
				{
					'name': 'hetang',
					'provider': 'hetang',
					'access_token': 'mytoken',
					'api_user': 'user@example.com',
				}
			]
		)
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', accounts)
		result = load_accounts_config()
		assert result is not None
		assert len(result) == 1
		assert result[0].provider == 'hetang'
		assert result[0].name == 'hetang'

	def test_missing_api_user(self, monkeypatch):
		accounts = json.dumps([{'name': 'test', 'access_token': 'token'}])
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', accounts)
		result = load_accounts_config()
		assert result is None

	def test_no_auth_method(self, monkeypatch):
		accounts = json.dumps([{'name': 'test', 'api_user': 'user@example.com'}])
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', accounts)
		result = load_accounts_config()
		assert result is None

	def test_invalid_json(self, monkeypatch):
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', 'not-json')
		result = load_accounts_config()
		assert result is None

	def test_not_array_format(self, monkeypatch):
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', '{"name": "test"}')
		result = load_accounts_config()
		assert result is None

	def test_hetang_account_finds_provider(self, monkeypatch):
		"""Regression test: hetang account should find its provider configuration."""
		accounts_data = json.dumps(
			[
				{
					'name': 'hetang',
					'provider': 'hetang',
					'access_token': 'mytoken',
					'api_user': 'user@example.com',
				}
			]
		)
		monkeypatch.setenv('ANYROUTER_ACCOUNTS', accounts_data)
		monkeypatch.delenv('PROVIDERS', raising=False)

		accounts = load_accounts_config()
		assert accounts is not None

		app_config = AppConfig.load_from_env()
		account = accounts[0]
		provider = app_config.get_provider(account.provider)

		assert provider is not None, f'Provider "{account.provider}" not found in configuration'
		assert provider.domain == 'https://hetang.lyvideo.top'
