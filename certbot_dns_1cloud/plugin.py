import logging
import requests
from certbot.plugins.dns_common import DNSAuthenticator
from certbot import util

import logging

logger = logging.getLogger("certbot_dns_1cloud")

def setup_logging(enable_verbose):
    """Настройка логирования с учетом уровня детализации."""
    if logger.hasHandlers():
        return  # Логгер уже настроен Certbot, не переопределяем его.

    logger.setLevel(logging.DEBUG if enable_verbose else logging.INFO)

    # Логи в файл
    file_handler = logging.FileHandler("plugin_debug.log", mode="w")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Логи в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

class Authenticator(DNSAuthenticator):
    """DNS Authenticator for 1cloud."""

    description = "Obtain certificates using a DNS TXT record (1cloud)."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.credentials = None
        self._setup_logging()

    @classmethod
    def add_parser_arguments(cls, add):
        super().add_parser_arguments(add)
        add("credentials", help="Path to 1cloud API credentials INI file")
        add(
            "dns-1cloud-logging",  # Новый аргумент для включения логов
            action="store_true",   # Булев флаг (включено/выключено)
            help="Enable detailed logging for the plugin (default: disabled)",
        )

    def _setup_logging(self):
        """Настраивает логгер для плагина."""
        # Проверка наличия пользовательского флага
        enable_debug = self.conf("dns-1cloud-logging")
        logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)

        # Настройка обработчиков (файл + консоль)
        if not logger.hasHandlers():
            # Логи в файл
            file_handler = logging.FileHandler("plugin_debug.log", mode="w")
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(file_handler)

            # Логи в консоль
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            logger.addHandler(console_handler)

    def more_info(self):
        return "This plugin configures a DNS TXT record to respond to DNS-01 challenges using the 1cloud API."

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "1cloud API credentials INI file",
            {
                "api_key": "API key for 1cloud API.",
                "api_url": "Base URL for 1cloud API (default: https://api.1cloud.ru).",
            },
        )
        logger.debug(f"Loaded dns_1cloud_api_key: {self.credentials.conf('api_key')}")
        logger.debug(f"Loaded dns_1cloud_api_url: {self.credentials.conf('api_url')}")

    def _perform(self, domain, validation_name, validation):
        logger.debug(f"Вызван _perform для домена {domain} с записью {validation_name}")
        domain_id = self._find_domain_id(domain)
        if not domain_id:
            logger.error(f"Домен {domain} не найден. Завершение с ошибкой.")
            raise Exception(f"Domain for {domain} not found in 1cloud.")
        logger.debug(f"Найден ID домена {domain_id} для {domain}")
        self._get_1cloud_client().add_txt_record(domain_id, validation_name, validation)

    def _cleanup(self, domain, validation_name, validation):
        logger.debug(f"Вызван _cleanup для домена {domain} с записью {validation_name}")
        domain_id = self._find_domain_id(domain)
        if not domain_id:
            logger.warning(f"Домен {domain} не найден. Удаление пропущено.")
            return
        
        logger.debug(f"Найден ID домена {domain_id} для {domain}. Удаляем запись.")
        try:
            self._get_1cloud_client().delete_txt_record(domain_id, validation_name)
        except Exception as e:
            logger.error(f"Ошибка при удалении записи: {e}")

    def _find_domain_id(self, domain):
        """Находит идентификатор домена второго уровня."""
        client = self._get_1cloud_client()
        domains = client.get_domains()
        domain_parts = domain.split(".")
        for i in range(len(domain_parts) - 1):
            possible_domain = ".".join(domain_parts[i:])
            for d in domains:
                if d["Name"] == possible_domain:
                    logger.debug(f"Найден домен {possible_domain} с ID {d['ID']}")
                    return d["ID"]
        logger.warning(f"Домен для {domain} не найден.")
        return None

    def _get_1cloud_client(self):
        return _1CloudClient(
            self.credentials.conf("api_key"),
            self.credentials.conf("api_url") or "https://api.1cloud.ru",
        )


class _1CloudClient:
    """Encapsulates all communication with the 1cloud API."""

    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def log_request(self, method, url, payload=None):
        """Логирует HTTP-запрос для отладки."""
        logger.debug(f"HTTP Method: {method}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request Headers: {self._headers()}")
        if payload:
            logger.debug(f"Request Payload: {payload}")

    def get_domains(self):
        """Получает список всех доменов."""
        url = f"{self.api_url}/dns"
        self.log_request("GET", url)
        response = requests.get(url, headers=self._headers())
        if response.status_code != 200:
            raise Exception(f"Failed to fetch domain list: {response.text}")
        return response.json()

    def get_records(self, domain_id):
        """Получает список записей для домена."""
        url = f"{self.api_url}/dns/{domain_id}"
        self.log_request("GET", url)
        response = requests.get(url, headers=self._headers())
        if response.status_code != 200:
            raise Exception(f"Failed to fetch domain records: {response.text}")
        return response.json()["LinkedRecords"]

    def add_txt_record(self, domain_id, record_name, record_content):
        """Добавляет TXT-запись на DNS серверах 1cloud."""
        create_url = f"{self.api_url}/dns/recordtxt"
        payload = {
            "DomainId": domain_id,
            "Name": record_name,
            "Text": record_content,
            "TTL": "300",
        }
        self.log_request("POST", create_url, payload)
        response = requests.post(create_url, headers=self._headers(), json=payload)
        if response.status_code != 200:
            logger.error(f"Failed to add TXT record: {response.status_code} - {response.text}")
            raise Exception(f"Failed to add TXT record: {response.text}")
        logger.info(f"Successfully added TXT record: {record_name} -> {record_content}")

    def delete_txt_record(self, domain_id, record_name):
        logger.debug(f"Попытка удаления всех TXT записей для {record_name} на домене {domain_id}")
        records = self.get_records(domain_id)

        # Убираем завершающую точку для сравнения, если она есть
        normalized_record_name = record_name.rstrip(".")

        matching_records = [
            r for r in records
            if r["TypeRecord"] == "TXT" and r["HostName"].rstrip(".") == normalized_record_name
        ]

        if not matching_records:
            logger.info(f"TXT записи для {record_name} уже отсутствуют на домене {domain_id}.")
            return

        for record in matching_records:
            record_id = record["ID"]
            url = f"{self.api_url}/dns/{domain_id}/{record_id}"
            self.log_request("DELETE", url)
            response = requests.delete(url, headers=self._headers())
            if response.status_code != 200:
                logger.error(f"Не удалось удалить TXT запись {record_name} с ID {record_id}: {response.text}")
                raise Exception(f"Failed to delete TXT record {record_name}: {response.text}")
            logger.info(f"Успешно удалена TXT запись {record_name} с ID {record_id}")