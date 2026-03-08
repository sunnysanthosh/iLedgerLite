/// App-wide configuration — all values overridable via --dart-define at build time.
///
/// Usage (Flutter):
///   flutter run --dart-define=AUTH_URL=https://api.staging.ledgerlite.app/auth
///   flutter build apk --dart-define=AUTH_URL=https://api.ledgerlite.app/auth
///
/// For CI / GitHub Actions, pass --dart-define flags in the build step:
///   flutter build apk \
///     --dart-define=AUTH_URL=$AUTH_URL \
///     --dart-define=USER_URL=$USER_URL \
///     ...
///
/// This file is the single source of truth for runtime-configurable values.
/// API URLs are also accessible via [ApiConstants] in core/api/api_constants.dart,
/// which reads from the same dart-define keys.
class AppConfig {
  AppConfig._();

  // ---------------------------------------------------------------------------
  // API service base URLs
  // Default values use 10.0.2.2 (Android emulator → host) on Docker Compose ports.
  // On a physical device replace with your machine's LAN IP or use a staging URL.
  // ---------------------------------------------------------------------------

  static const String authServiceUrl = String.fromEnvironment(
    'AUTH_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const String userServiceUrl = String.fromEnvironment(
    'USER_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );

  static const String transactionServiceUrl = String.fromEnvironment(
    'TXN_URL',
    defaultValue: 'http://10.0.2.2:8003',
  );

  static const String ledgerServiceUrl = String.fromEnvironment(
    'LEDGER_URL',
    defaultValue: 'http://10.0.2.2:8004',
  );

  static const String reportServiceUrl = String.fromEnvironment(
    'REPORT_URL',
    defaultValue: 'http://10.0.2.2:8005',
  );

  static const String aiServiceUrl = String.fromEnvironment(
    'AI_URL',
    defaultValue: 'http://10.0.2.2:8006',
  );

  static const String notificationServiceUrl = String.fromEnvironment(
    'NOTIFICATION_URL',
    defaultValue: 'http://10.0.2.2:8007',
  );

  static const String syncServiceUrl = String.fromEnvironment(
    'SYNC_URL',
    defaultValue: 'http://10.0.2.2:8008',
  );
}
