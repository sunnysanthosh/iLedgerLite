/// App-wide API base URLs — all values overridable via --dart-define at build time.
///
/// Usage (Flutter):
///   flutter run \
///     --dart-define=AUTH_URL=https://api.staging.ledgerlite.app/auth \
///     --dart-define=USER_URL=https://api.staging.ledgerlite.app/user
///
///   flutter build apk \
///     --dart-define=AUTH_URL=https://api.ledgerlite.app/auth
///
/// Defaults use 10.0.2.2 (Android emulator loopback → host machine) on the
/// same Docker Compose ports as the backend services.
class ApiConstants {
  ApiConstants._();

  static const String authBase = String.fromEnvironment(
    'AUTH_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const String userBase = String.fromEnvironment(
    'USER_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );

  static const String transactionBase = String.fromEnvironment(
    'TXN_URL',
    defaultValue: 'http://10.0.2.2:8003',
  );

  static const String ledgerBase = String.fromEnvironment(
    'LEDGER_URL',
    defaultValue: 'http://10.0.2.2:8004',
  );

  static const String reportBase = String.fromEnvironment(
    'REPORT_URL',
    defaultValue: 'http://10.0.2.2:8005',
  );

  static const String aiBase = String.fromEnvironment(
    'AI_URL',
    defaultValue: 'http://10.0.2.2:8006',
  );

  static const String notificationBase = String.fromEnvironment(
    'NOTIFICATION_URL',
    defaultValue: 'http://10.0.2.2:8007',
  );

  static const String syncBase = String.fromEnvironment(
    'SYNC_URL',
    defaultValue: 'http://10.0.2.2:8008',
  );
}
