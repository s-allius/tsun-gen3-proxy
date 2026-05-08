# Inverter Proxy Server

A high-performance, asynchronous proxy server built with [Quart](https://quart.palletsprojects.com/) to manage and monitor solar inverters (TSUN, Solarman). It bridges inverter data to your local network and integrates seamlessly with Home Assistant.

## 🚀 Features

- **Multi-Generation Support:** Handles TSUN (Gen3) and Solarman (Gen3Plus) protocols.
- **Asynchronous Core:** Built on `asyncio` for efficient handling of multiple concurrent inverter connections.
- **Home Assistant Ready:** Automated discovery and PR generation for Home Assistant integration.
- **Health Monitoring:** Dedicated endpoints for service and hardware health checks.
- **Flexible Configuration:** Support for TOML, JSON, and Environment Variables.

---

## 🛠 Network & Port Assignments

The server listens on the following ports:

| Port | Protocol | Description |
| :--- | :--- | :--- |
| **8127** | HTTP | Web Dashboard & Health Check API (Quart) |
| **5005** | TCP | Inverter Listener for **TSUN (Gen3)** |
| **10000** | TCP | Inverter Listener for **Solarman (Gen3Plus)** |

---

## ⚙️ Configuration

The application loads configuration in the following priority:

1. `cnf/default_config.toml` (Defaults)
2. Environment Variables (e.g., `LOG_LVL`, `SERVICE_NAME`)
3. `config.json` / `config.toml` in the config directory.
4. Custom files passed via CLI arguments.

### Environment Variables

- `LOG_LVL`: Set to `DEBUG`, `INFO`, `WARN`, or `ERROR`.
- `SERVICE_NAME`: The name identifying this instance (default: `proxy`).
- `SLUG` / `HOSTNAME`: Used for Home Assistant Add-on identification.

---

## 🚦 API Endpoints

### Health Checks

- **`GET /-/ready`**: Returns `200 OK` if the proxy service is initialized and ready to accept connections.
- **`GET /-/healthy`**: Performs a deep check, verifying the connection status of all configured inverters. Returns `503` if any inverter reports a problem.

---

## 💻 CLI Usage

You can start the server with custom paths:

```bash
python server.py --config_path ./my_configs/ --log_path ./logs/ --log_backups 7
```

**Available Arguments:**

- `-c, --config_path`: Path for configuration files (default: `./config/`).
- `-j, --json_config`: Direct path to a user JSON config.
- `-t, --toml_config`: Direct path to a user TOML config.
- `-l, --log_path`: Directory for log files.
- `-tr, --trans_path`: Path for translation files.
- `-r, --rel_urls`: Use relative URLs in the dashboard.

---

## 📦 Deployment & CI/CD

We use the **GitLab Flow** strategy.

- **Feature Development:** Use feature branches, merge via PR to `main`.
- **Releases:** Creating a tag like `v1.2.0-rc1` or `v1.2.0-rel` triggers a GitHub Action that:
  1. Builds the Docker container.
  2. Packages the Home Assistant Add-on.
  3. Signs the images and creates a PR for the Home Assistant Repository.

---
*This project is part of the solar-monitoring ecosystem. For issues or feature requests, please open a GitHub Issue.*
