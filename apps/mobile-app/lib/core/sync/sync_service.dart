import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../api/api_client.dart';
import 'local_database.dart';

final syncServiceProvider = Provider<SyncService>((ref) {
  return SyncService(
    apiClient: ref.watch(apiClientProvider),
    localDb: ref.watch(localDatabaseProvider),
  );
});

/// Sync status exposed as a stream to the UI.
final syncStatusProvider =
    StreamProvider.autoDispose<SyncStatus>((ref) {
  final service = ref.watch(syncServiceProvider);
  return service.statusStream;
});

enum SyncState { idle, syncing, error, done }

class SyncStatus {
  const SyncStatus({
    this.state = SyncState.idle,
    this.pendingCount = 0,
    this.lastSyncTime,
    this.errorMessage,
  });

  final SyncState state;
  final int pendingCount;
  final String? lastSyncTime;
  final String? errorMessage;
}

class SyncService {
  SyncService({
    required ApiClient apiClient,
    required LocalDatabase localDb,
  })  : _apiClient = apiClient,
        _localDb = localDb;

  final ApiClient _apiClient;
  final LocalDatabase _localDb;

  final _controller = StreamController<SyncStatus>.broadcast();
  Stream<SyncStatus> get statusStream => _controller.stream;

  Timer? _periodicTimer;

  /// Start a background periodic sync every [interval].
  void startPeriodicSync({Duration interval = const Duration(minutes: 5)}) {
    _periodicTimer?.cancel();
    _periodicTimer = Timer.periodic(interval, (_) => sync());
  }

  void stopPeriodicSync() {
    _periodicTimer?.cancel();
    _periodicTimer = null;
  }

  /// Run a full push-then-pull sync cycle.
  Future<void> sync() async {
    final pending = await _localDb.pendingCount();
    _controller.add(SyncStatus(state: SyncState.syncing, pendingCount: pending));

    try {
      // 1. Push unsynced local changes
      await _pushChanges();

      // 2. Pull remote changes
      await _pullChanges();

      // 3. Update last sync time
      final now = DateTime.now().toUtc().toIso8601String();
      await _localDb.setLastSyncTime(now);

      final remaining = await _localDb.pendingCount();
      _controller.add(SyncStatus(
        state: SyncState.done,
        pendingCount: remaining,
        lastSyncTime: now,
      ));
    } catch (e) {
      debugPrint('Sync error: $e');
      final count = await _localDb.pendingCount();
      final lastSync = await _localDb.getLastSyncTime();
      _controller.add(SyncStatus(
        state: SyncState.error,
        pendingCount: count,
        lastSyncTime: lastSync,
        errorMessage: e.toString(),
      ));
    }
  }

  Future<void> _pushChanges() async {
    final unsyncedTxns = await _localDb.getUnsyncedTransactions();
    final unsyncedLedger = await _localDb.getUnsyncedLedgerEntries();

    if (unsyncedTxns.isEmpty && unsyncedLedger.isEmpty) return;

    final deviceId = 'flutter-mobile'; // simplified device ID
    final payload = {
      'device_id': deviceId,
      'transactions': unsyncedTxns,
      'ledger_entries': unsyncedLedger,
    };

    final response = await _apiClient.syncPush(payload);
    if (response.statusCode == 200) {
      final txnIds = unsyncedTxns.map((t) => t['id'] as String).toList();
      final ledgerIds =
          unsyncedLedger.map((l) => l['id'] as String).toList();
      await _localDb.markTransactionsSynced(txnIds);
      await _localDb.markLedgerEntriesSynced(ledgerIds);
    }
  }

  Future<void> _pullChanges() async {
    final lastSync = await _localDb.getLastSyncTime();
    final deviceId = 'flutter-mobile';
    final response =
        await _apiClient.syncPull(deviceId, since: lastSync);

    if (response.statusCode == 200) {
      final data = response.data as Map<String, dynamic>;
      final transactions =
          (data['transactions'] as List?)?.cast<Map<String, dynamic>>() ?? [];
      final ledgerEntries =
          (data['ledger_entries'] as List?)?.cast<Map<String, dynamic>>() ?? [];

      for (final txn in transactions) {
        await _localDb.upsertTransaction(txn, synced: true);
      }
      for (final entry in ledgerEntries) {
        await _localDb.upsertLedgerEntry(entry, synced: true);
      }
    }
  }

  void dispose() {
    _periodicTimer?.cancel();
    _controller.close();
  }
}
