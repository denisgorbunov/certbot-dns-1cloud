# Certbot DNS-1Cloud Plugin

The **Certbot DNS-1Cloud** plugin automates the process of performing DNS-01 challenges using the 1Cloud API. It is useful for obtaining Let's Encrypt certificates for domains managed in 1Cloud.

---

## Installation

### Requirements
- Python 3.7+
- Certbot
- pip (Python package manager)
- 1Cloud account with API access

### Steps to Install

1. **Install the plugin from the Git repository:**

   ```bash
   pip install git+https://github.com/denisgorbunov/certbot-dns-1cloud.git
   ```

2. **Verify plugin installation:**

   Run the following command to check if the plugin is available:
   ```bash
   certbot plugins
   ```
   You should see `dns-1cloud` listed as an available plugin.

---

## Configuration

### Step 1: Create API Credentials
1. Log in to your 1Cloud account.
2. Generate an API key.
3. Save the API key securely; it will be used for DNS management.

### Step 2: Create a Credentials File
1. Create a file to store your 1Cloud API credentials, e.g., `/path/to/1cloud.ini`.
2. Add the following content to the file:

   ```ini
   dns_1cloud_api_key = <your-api-key>
   dns_1cloud_api_url = https://api.1cloud.ru  # Default API URL
   ```
   Replace `<your-api-key>` with your actual API key.

3. Secure the file by restricting access:

   ```bash
   chmod 600 /path/to/1cloud.ini
   ```

---

## Usage

### Step 1: Run Certbot with the Plugin
Use the following command to issue a certificate:

```bash
sudo certbot certonly \
  --authenticator dns-1cloud \
  --dns-1cloud-credentials /path/to/1cloud.ini \
  -d "*.example.com" -d "example.com" \
  --dns-1cloud-propagation-seconds 60 \
  --dry-run
```

### Explanation of Flags
- `--authenticator dns-1cloud`: Specifies the plugin for DNS-based challenges.
- `--dns-1cloud-credentials`: Path to the 1Cloud API credentials file.
- `-d`: Specifies the domain names for the certificate.
- `--dns-1cloud-propagation-seconds`: Time to wait for DNS changes to propagate (default: 60 seconds).
- `--dry-run`: Simulates the process without actually issuing a certificate.

### Step 2: Automate Certificate Renewal
Certbot automatically sets up a cron job or systemd timer to renew certificates. Ensure the plugin is configured correctly for automated renewals by including the `--authenticator dns-1cloud` and credentials flags in your Certbot commands.

To test the renewal process, run:
```bash
sudo certbot renew --dry-run
```

---

## Logging
This plugin provides detailed logging to help troubleshoot issues. Logs are saved to `plugin_debug.log` in the current directory. To enable verbose logging for Certbot:

```bash
sudo certbot certonly \
  --authenticator dns-1cloud \
  --dns-1cloud-credentials /path/to/1cloud.ini \
  -d "*.example.com" -d "example.com" \
  --verbose
```

---

## Troubleshooting

### Common Issues
1. **Error: "Domain not found":**
   - Ensure the domain is registered and managed in 1Cloud.
   - Verify the API credentials.

2. **Error: "TXT record not found":**
   - Increase the propagation time with `--dns-1cloud-propagation-seconds`.
   - Check if your DNS provider caches records excessively.

3. **Permission Denied for `1cloud.ini`:**
   - Make sure the credentials file is readable by the Certbot process.

---

## Development

To modify or contribute to the plugin:

1. Clone the repository:
   ```bash
   git clone https://github.com/denisgorbunov/certbot-dns-1cloud.git
   cd certbot-dns-1cloud
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests (if available):
   ```bash
   pytest
   ```

---

## License

This plugin is licensed under the MIT License. See the `LICENSE` file for more information.

---

## Support
For questions or issues, please open a ticket in the GitHub repository or contact the maintainers.
