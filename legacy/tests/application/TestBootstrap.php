<?php

/**
 * Unified Test Bootstrap for LibreTime Legacy Tests
 * 
 * This file provides a single entry point for all PHPUnit tests.
 * It handles environment setup, constant definitions, and proper
 * initialization for CLI test environment (where gettext is unavailable).
 */

// Error reporting
error_reporting(E_ALL | E_STRICT);
ini_set('display_errors', '1');

// ============================================================================
// Path Resolution (support both Docker and native environments)
// ============================================================================

$testDir = __DIR__;
$applicationPath = dirname($testDir, 2) . '/application';

if (!is_dir($applicationPath)) {
    // Docker path fallback
    $applicationPath = '/app/application';
}

if (!is_dir($applicationPath)) {
    throw new Exception('Cannot find application path. Tried: ' . dirname($testDir, 2) . '/application, /app/application');
}

// ============================================================================
// Define Application Environment early (needed before loading conf.php)
// Other constants are defined by constants.php which is loaded via conf.php
// ============================================================================

if (!defined('APPLICATION_ENV')) {
    define('APPLICATION_ENV', getenv('APPLICATION_ENV') ?: 'testing');
}

// ============================================================================
// Gettext Shim for CLI Environment
// Zend_Navigation and views use _() for translations, but gettext isn't
// available in CLI. We provide a passthrough shim.
// ============================================================================

if (!function_exists('_')) {
    /**
     * Gettext shim for CLI test environment.
     * Returns the input string unchanged (passthrough).
     */
    function _($string) {
        return $string;
    }
}

if (!function_exists('gettext')) {
    function gettext($string) {
        return $string;
    }
}

// ============================================================================
// Include Paths (set up before loading dependencies)
// ============================================================================

$rootPath = dirname($applicationPath);
$vendorPath = $rootPath . '/vendor';
$includePaths = [
    $rootPath . '/library',
    $vendorPath,
    $vendorPath . '/zf1s/zend-loader/library',
    $vendorPath . '/libretime/propel1/runtime/lib',
    $applicationPath . '/common',
    $applicationPath . '/models',
    $applicationPath . '/services',
    $applicationPath . '/controllers',
    $applicationPath . '/controllers/plugins',
    $applicationPath . '/logging',
    $testDir . '/testdata',
    $testDir . '/helpers',
];

foreach ($includePaths as $path) {
    if (is_dir($path)) {
        set_include_path($path . PATH_SEPARATOR . get_include_path());
    }
}

// ============================================================================
// Autoloader and Dependencies
// ============================================================================

require_once $vendorPath . '/autoload.php';

// Load configuration (this defines remaining constants like CONFIG_PATH, etc.)
require_once $applicationPath . '/configs/conf.php';
require_once $applicationPath . '/configs/ACL.php';

// ============================================================================
// Propel Initialization
// ============================================================================

require_once 'libretime/propel1/runtime/lib/Propel.php';

if (!isset($configRun) || !$configRun) {
    Propel::init(PROPEL_CONFIG_FILEPATH);
}

// ============================================================================
// Logging Setup
// ============================================================================

require_once $applicationPath . '/logging/Logging.php';
Logging::setLogPath(LIBRETIME_LOG_FILEPATH);

// ============================================================================
// Navigation (gettext shim already defined above)
// ============================================================================

if (file_exists(CONFIG_PATH . '/navigation.php')) {
    require_once CONFIG_PATH . '/navigation.php';
}

// ============================================================================
// Session Configuration (minimal for testing)
// Note: Session is NOT started here to avoid "headers already sent" errors.
// Tests that need sessions should call Zend_Session::start() in setUp()
// ============================================================================

Zend_Session::setOptions([
    'strict' => false,
    'use_cookies' => false,
    'use_only_cookies' => false,
]);

// ============================================================================
// Test Helper Auto-loader
// ============================================================================

require_once $testDir . '/helpers/TestHelper.php';
require_once $testDir . '/helpers/AirtimeInstall.php';
