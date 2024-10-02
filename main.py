from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException, TimeoutException
from fake_useragent import UserAgent
import pandas as pd
from selenium.webdriver.chrome.service import Service
import yaml
from pathlib import Path
import re
import click

from utils.linkedIn_authenticator import LinkedInAuthenticator
from utils.linkedIn_bot_facade import LinkedInBotFacade

class ConfigError(Exception):
    pass

class ConfigValidator:
    @staticmethod
    def validate_email(email):
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    @staticmethod
    def validate_yaml_file(yaml_path):
        try:
            with open(yaml_path, 'r') as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"File not found: {yaml_path}")
    
    
    def validate_config(config_yaml_path):
        parameters = ConfigValidator.validate_yaml_file(config_yaml_path)
        print(parameters['experience'].keys())
        required_keys = {
            'title': str,
            'company_name': str,
            'start_month': str,
            'start_year': int,
            'end_month': str,
            'end_year': int,
            'current_working': bool,
        }

        for key, expected_type in required_keys.items():
            if key not in parameters:
                if key in ['companyBlacklist', 'titleBlacklist']:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Missing or invalid key '{key}' in config file {config_yaml_path}")
            elif not isinstance(parameters[key], expected_type):
                if key in ['companyBlacklist', 'titleBlacklist'] and parameters[key] is None:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Invalid type for key '{key}' in config file {config_yaml_path}. Expected {expected_type}.")

        return parameters

    @staticmethod
    def validate_secrets(secrets_yaml_path):
        secrets = ConfigValidator.validate_yaml_file(secrets_yaml_path)
        mandatory_secrets = ['email', 'password']

        for secret in mandatory_secrets:
            if secret not in secrets:
                raise ConfigError(f"Missing secret '{secret}' in file {secrets_yaml_path}")

        if not ConfigValidator.validate_email(secrets['email']):
            raise ConfigError(f"Invalid email format in secrets file {secrets_yaml_path}.")
        if not secrets['password']:
            raise ConfigError(f"Password cannot be empty in secrets file {secrets_yaml_path}.")

        return secrets['email'], str(secrets['password'])

class FileManager:
    @staticmethod
    def find_file(name_containing, with_extension, at_path):
        return next((file for file in at_path.iterdir() if name_containing.lower() in file.name.lower() and file.suffix.lower() == with_extension.lower()), None)

    @staticmethod
    def validate_data_folder(app_data_folder):
        if not app_data_folder.exists() or not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")

        required_files = ['secrets.yaml', 'userprofile.yaml']
        missing_files = [file for file in required_files if not (app_data_folder / file).exists()]
        
        if missing_files:
            raise FileNotFoundError(f"Missing files in the data folder: {', '.join(missing_files)}")

        # output_folder = app_data_folder / 'output'
        # output_folder.mkdir(exist_ok=True)
        return (app_data_folder / 'secrets.yaml', app_data_folder / 'userprofile.yaml')

def init_browser():
    try:
        ua = UserAgent()
        userAgent = ua.chrome

        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={userAgent}')

        path = ChromeDriverManager().install()
        return webdriver.Chrome(service=Service(path), options=chrome_options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")

def run_bot(email,password):
    try:
        browser = init_browser()
        login_component = LinkedInAuthenticator(browser)
        bot = LinkedInBotFacade(login_component)
        bot.set_secrets(email, password)
        bot.start_login()
    except WebDriverException as e:
        print(f"WebDriver error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"Error running the bot: {str(e)}")


@click.command()
@click.option('--resume', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path), help="Path to the resume PDF file")
def main(resume):
    try:
        data_folder = Path("metadata")
        secrets_file, config_file = FileManager.validate_data_folder(data_folder)
        
        parameters = ConfigValidator.validate_config(config_file)
        email, password = ConfigValidator.validate_secrets(secrets_file)

        # run_bot(email, password, parameters)
    except ConfigError as ce:
        print(f"Configuration error: {str(ce)}")
        print("Refer to the configuration guide for troubleshooting: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except FileNotFoundError as fnf:
        print(f"File not found: {str(fnf)}")
        print("Ensure all required files are present in the data folder.")
        print("Refer to the file setup guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except RuntimeError as re:

        print(f"Runtime error: {str(re)}")

        print("Refer to the configuration and troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Refer to the general troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")

if __name__ == "__main__":
    main()

