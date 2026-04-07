# LibreTime Legacy Testing Guide

> **Docker-based testing environment** — no local PHP 7.4 installation required.

## Quick Start

```bash
# Build the Docker image (first time only)
./test.sh build

# Run all tests
./test.sh

# Generate coverage report
./test.sh coverage
```

## Requirements

- Docker Engine 20.10+
- Docker Compose 1.29+
- ~500MB free disk space for images

## Available Commands

| Command | Description |
|---------|-------------|
| `./test.sh build` | Build Docker test image |
| `./test.sh test` | Run all PHPUnit tests (default) |
| `./test.sh coverage` | Generate HTML coverage report |
| `./test.sh shell` | Interactive shell for debugging |
| `./test.sh up` | Start PostgreSQL in background |
| `./test.sh down` | Stop test environment |
| `./test.sh clean` | Remove all containers/volumes |
| `./test.sh phpunit --filter TestName` | Run specific test |

## Project Structure

```
legacy/
├── Dockerfile.test           # PHP 7.4 test image
├── docker-compose.test.yml   # Services orchestration
├── test.sh                   # Main test runner script
├── Makefile.test             # Make targets for Docker
├── TESTING.md                # This file
├── tests/
│   ├── config/
│   │   └── config.yml        # Test configuration
│   ├── phpunit.xml           # PHPUnit configuration
│   └── sql/init/             # Database initialization
└── coverage/                 # Generated coverage reports
```

## How It Works

### Services

1. **postgres** — PostgreSQL 12 with test database
   - Database: `airtimeunittests`
   - User: `libretime` / Password: `libretime`
   - Ports: `5432` (mapped to host)

2. **php** — PHP 7.4 CLI with all extensions
   - Pre-installed: `pdo_pgsql`, `xdebug`, `composer`
   - Source mounted for live editing

3. **test** — One-shot test runner (for CI)

4. **coverage** — Coverage report generator

5. **shell** — Interactive debugging container

### Test Configuration

Test configuration is in `tests/config/config.yml`:

```yaml
database:
  host: postgres      # Docker service name
  port: 5432
  name: airtimeunittests
  user: libretime
  password: libretime
```

### Database Initialization

PostgreSQL schema is initialized automatically:
1. Docker entrypoint creates database
2. Tests call `TestHelper::installTestDatabase()` to create tables via Propel

## Writing Tests

### Unit Test (no database)

```php
<?php
class MyServiceUnitTest extends PHPUnit_Framework_TestCase
{
    public function testSomething()
    {
        $service = new Application_Service_MyService();
        $result = $service->doSomething();
        $this->assertEquals('expected', $result);
    }
}
```

### Database Test (with Propel)

```php
<?php
class MyModelDbTest extends Zend_Test_PHPUnit_DatabaseTestCase
{
    public function setUp()
    {
        TestHelper::installTestDatabase();
        TestHelper::setupZendBootstrap();
        parent::setUp();
    }

    public function getConnection()
    {
        $config = TestHelper::getDbZendConfig();
        $connection = Zend_Db::factory('pdo_pgsql', $config);
        return $this->createZendDbConnection($connection, 'airtimeunittests');
    }

    public function getDataSet()
    {
        return new PHPUnit_Extensions_Database_DataSet_YamlDataSet(
            __DIR__ . '/datasets/my_fixture.yml'
        );
    }

    public function testSomething()
    {
        TestHelper::loginUser();
        $model = new Application_Model_MyModel();
        $this->assertTrue($model->doSomething());
    }
}
```

## Debugging

### Interactive Shell

```bash
./test.sh shell
# Inside container:
> ../vendor/bin/phpunit --filter MyTest
> php -r "var_dump(new Application_Model_Show());"
```

### Check Database

```bash
# From host with psql client:
psql -h localhost -U libretime -d airtimeunittests

# Or from container:
./test.sh shell
> psql -h postgres -U libretime -d airtimeunittests
```

### View Logs

```bash
# Test logs
ls tests/log/

# Docker logs
docker-compose -f docker-compose.test.yml logs -f postgres
```

## Coverage Reports

```bash
./test.sh coverage
# Opens in browser:
open coverage/index.html
```

Coverage excludes:
- Propel generated models (`om/`, `map/`)
- Bootstrap and error controller
- View scripts (`.phtml`)

## CI/CD Integration

GitHub Actions example:

```yaml
name: Legacy Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build test image
        run: ./test.sh build
      
      - name: Run tests
        run: ./test.sh test
      
      - name: Generate coverage
        run: ./test.sh coverage
      
      - name: Upload coverage
        uses: actions/upload-artifact@v3
        with:
          name: coverage
          path: legacy/coverage/
```

## Troubleshooting

### Tests fail with "Connection refused"

PostgreSQL is still starting. Wait a moment and retry:
```bash
./test.sh down
./test.sh test
```

### Permission denied on test.sh

```bash
chmod +x test.sh
```

### Container already exists

```bash
./test.sh clean
./test.sh build
```

### Out of disk space

```bash
./test.sh clean
docker system prune -a
```

## Architecture Notes

- **Frozen dependencies**: PHP 7.4, ZF1, Propel 1.6 locked
- **No host dependencies**: Everything runs in containers
- **Volume mounts**: Source code mounted read-only, tests writable
- **Network isolation**: Services communicate via Docker network
- **Ephemeral data**: PostgreSQL data in named volume (persisted until `clean`)

## Known Issues

1. **PHPUnit 5.7 is deprecated** — cannot upgrade (compatibility)
2. **Propel requires DB connection** — no true unit tests for models
3. **Coverage needs Xdebug 2.9** — slower than pcov but required for PHP 7.4
4. **Zend_Session warnings** — can be ignored in CLI context

## Migration from Local Testing

If you previously ran tests locally:

```bash
# Old way (requires PHP 7.4 locally):
# cd tests && ../vendor/bin/phpunit

# New way (Docker):
./test.sh
```

Add to your shell for convenience:
```bash
alias lt-test='cd /path/to/libretime/legacy && ./test.sh'
alias lt-coverage='cd /path/to/libretime/legacy && ./test.sh coverage'
alias lt-shell='cd /path/to/libretime/legacy && ./test.sh shell'
```
