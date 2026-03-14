import 'dart:io';

import 'package:flutter/services.dart';

/// Manages TLS certificate pinning for production HTTPS connections.
///
/// Enabled via dart-define at build time:
///   --dart-define=CERT_PIN_ENABLED=true
///
/// When enabled, the Dio HTTP client is restricted to trust only the ISRG Root X1
/// CA (the root used by Let's Encrypt). Connections to any host whose certificate
/// was not issued by ISRG Root X1 will be rejected at the TLS handshake.
///
/// Development / staging builds leave [isEnabled] false (default) and skip pinning
/// so that local HTTP (10.0.2.2) and staging self-signed Let's Encrypt certs work.
///
/// Usage — call once at app startup before building any Dio clients:
///   await CertificatePinning.init();
class CertificatePinning {
  CertificatePinning._();

  /// Set to true by passing --dart-define=CERT_PIN_ENABLED=true at build time.
  static const bool isEnabled = bool.fromEnvironment('CERT_PIN_ENABLED', defaultValue: false);

  static SecurityContext? _context;

  /// The pinned [SecurityContext], or null if pinning is disabled.
  static SecurityContext? get context => _context;

  /// Loads the pinned CA certificate from the app bundle.
  /// No-op when [isEnabled] is false.
  /// Must be called once before any Dio client is constructed.
  static Future<void> init() async {
    if (!isEnabled) return;

    final pem = await rootBundle.load('assets/certs/isrg_root_x1.pem');
    final ctx = SecurityContext(withTrustedRoots: false)
      ..setTrustedCertificatesBytes(pem.buffer.asUint8List());
    _context = ctx;
  }
}
