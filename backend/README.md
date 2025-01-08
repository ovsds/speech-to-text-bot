# Speech To Text Bot Backend

## Usage

### Settings

#### Application

- `APP__ENV` - application environment, can be one of `development`, `testing`, `staging`, `production`. Default is `production`.
- `APP__DEBUG` - application debug mode, can be `true` or `false`. Default is `false`.

#### Logging

- `LOGS__LEVEL` - logging level, can be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`. Default is `INFO`.
- `LOGS__FORMAT` - logging format string, passed to python logging formatter. Default is `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.

#### Server

- `SERVER__HOST` - server host. Default is `localhost`.
- `SERVER__PORT` - server port. Default is `8080`.
- `SERVER__PUBLIC_HOST` - server public host.

#### Telegram

- `TELEGRAM__TOKEN` - bot token.
- `TELEGRAM__BOT_NAME` - bot name.
- `TELEGRAM__BOT_SHORT_DESCRIPTION` - bot short description.
- `TELEGRAM__BOT_DESCRIPTION` - bot description.
- `TELEGRAM__ADMIN_IDS` - list of admin ids.
- `TELEGRAM__ALLOWED_USER_IDS` - list of allowed user ids.
- `TELEGRAM__WEBHOOK_ENABLED` - webhook enabled, can be `true` or `false`. Default is `true`.
- `TELEGRAM__WEBHOOK_URL` - webhook url.
- `TELEGRAM__SECRET_TOKEN` - webhook secret token.

#### Other

- `THREAD_POOL_EXECUTOR_MAX_WORKERS` - thread pool executor(used for sync tasks) max workers. Default is `10`.
- `SETTINGS_PATH` - paths to setting files, separated by `:`.

## Development

### Global dependencies

- [poetry](https://python-poetry.org/docs/#installation)
- [trivy](https://trivy.dev/latest/getting-started/installation/) - used for security scanning

### Taskfile commands

For all commands see [Taskfile](Taskfile.yaml) or `task --list-all`.
