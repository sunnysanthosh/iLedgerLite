class ApiConstants {
  ApiConstants._();

  // Default to local Docker Compose ports.
  // Override via environment or build config for staging/production.
  static const String authBase = String.fromEnvironment(
    'AUTH_BASE_URL',
    defaultValue: 'http://10.0.2.2:8001',
  );

  static const String userBase = String.fromEnvironment(
    'USER_BASE_URL',
    defaultValue: 'http://10.0.2.2:8002',
  );

  static const String transactionBase = String.fromEnvironment(
    'TRANSACTION_BASE_URL',
    defaultValue: 'http://10.0.2.2:8003',
  );

  static const String ledgerBase = String.fromEnvironment(
    'LEDGER_BASE_URL',
    defaultValue: 'http://10.0.2.2:8004',
  );

  static const String reportBase = String.fromEnvironment(
    'REPORT_BASE_URL',
    defaultValue: 'http://10.0.2.2:8005',
  );

  static const String syncBase = String.fromEnvironment(
    'SYNC_BASE_URL',
    defaultValue: 'http://10.0.2.2:8008',
  );
}
