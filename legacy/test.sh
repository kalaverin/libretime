#!/bin/bash
# LibreTime Legacy Test Runner
# Docker-based testing for frozen PHP 7.4 project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}LibreTime Legacy Test Runner (Docker)${NC}"
echo "========================================"

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker-compose -f docker-compose.test.yml down -v 2>/dev/null || true
}

# Parse command
case "${1:-test}" in
    build)
        echo -e "${GREEN}Building test environment...${NC}"
        docker-compose -f docker-compose.test.yml build
        ;;
    
    test|run)
        echo -e "${GREEN}Running tests...${NC}"
        docker-compose -f docker-compose.test.yml run --rm test
        ;;
    
    coverage)
        echo -e "${GREEN}Generating coverage report...${NC}"
        mkdir -p coverage
        docker-compose -f docker-compose.test.yml run --rm coverage
        echo -e "${GREEN}Coverage report saved to ./coverage/${NC}"
        ;;
    
    shell)
        echo -e "${GREEN}Starting interactive shell...${NC}"
        docker-compose -f docker-compose.test.yml run --rm shell
        ;;
    
    up)
        echo -e "${GREEN}Starting test environment (detached)...${NC}"
        docker-compose -f docker-compose.test.yml up -d postgres
        echo -e "${GREEN}Waiting for PostgreSQL...${NC}"
        sleep 3
        docker-compose -f docker-compose.test.yml ps
        echo -e "\n${YELLOW}Services running. Use './test.sh shell' for interactive access.${NC}"
        ;;
    
    down)
        echo -e "${GREEN}Stopping test environment...${NC}"
        docker-compose -f docker-compose.test.yml down
        ;;
    
    clean)
        echo -e "${YELLOW}Removing all test containers and volumes...${NC}"
        docker-compose -f docker-compose.test.yml down -v --remove-orphans
        docker system prune -f
        echo -e "${GREEN}Cleanup complete.${NC}"
        ;;
    
    watch)
        echo -e "${GREEN}Running tests in watch mode (re-run on file change)...${NC}"
        echo -e "${YELLOW}Note: Requires entr to be installed in container${NC}"
        docker-compose -f docker-compose.test.yml run --rm shell -c "
            cd /app &&
            find tests application -name '*.php' | entr -r vendor/bin/phpunit --configuration tests/phpunit.xml
        "
        ;;
    
    phpunit)
        # Pass all arguments to phpunit
        shift
        echo -e "${GREEN}Running: phpunit $@${NC}"
        docker-compose -f docker-compose.test.yml run --rm test ../vendor/bin/phpunit "$@"
        ;;
    
    help|--help|-h)
        cat << EOF
LibreTime Legacy Test Runner (Docker-based)

Usage: ./test.sh [command]

Commands:
    build       Build the Docker test image
    test|run    Run all tests (default)
    coverage    Generate HTML coverage report in ./coverage/
    shell       Start interactive bash shell in test container
    up          Start test environment (postgres) in background
    down        Stop test environment
    clean       Remove all containers, volumes, and prune
    watch       Run tests in watch mode (re-run on file change)
    phpunit     Pass arguments directly to phpunit
    help        Show this help message

Examples:
    ./test.sh                    # Run all tests
    ./test.sh coverage           # Generate coverage report
    ./test.sh shell              # Interactive shell for debugging
    ./test.sh phpunit --filter BlockDbTest  # Run specific test

Environment:
    Tests run against PostgreSQL 12 in Docker.
    No local PHP/PostgreSQL installation required.
EOF
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run './test.sh help' for usage."
        exit 1
        ;;
esac
