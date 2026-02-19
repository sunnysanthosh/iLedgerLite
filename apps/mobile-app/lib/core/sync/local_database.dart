import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

final localDatabaseProvider = Provider<LocalDatabase>((ref) {
  return LocalDatabase();
});

class LocalDatabase {
  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'ledgerlite_local.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE transactions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        category_id TEXT,
        type TEXT NOT NULL,
        amount TEXT NOT NULL,
        description TEXT,
        transaction_date TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE ledger_entries (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        customer_id TEXT NOT NULL,
        type TEXT NOT NULL,
        amount TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        is_settled INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE customers (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        address TEXT,
        outstanding_balance TEXT NOT NULL DEFAULT '0.00',
        synced INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE sync_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
      )
    ''');

    await db.execute(
        'CREATE INDEX idx_txn_synced ON transactions(synced)');
    await db.execute(
        'CREATE INDEX idx_ledger_synced ON ledger_entries(synced)');
  }

  // --- Transactions ---
  Future<List<Map<String, dynamic>>> getUnsyncedTransactions() async {
    final db = await database;
    return db.query('transactions', where: 'synced = 0');
  }

  Future<void> upsertTransaction(Map<String, dynamic> data,
      {bool synced = true}) async {
    final db = await database;
    await db.insert(
      'transactions',
      {...data, 'synced': synced ? 1 : 0},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> markTransactionsSynced(List<String> ids) async {
    final db = await database;
    for (final id in ids) {
      await db.update('transactions', {'synced': 1},
          where: 'id = ?', whereArgs: [id]);
    }
  }

  // --- Ledger entries ---
  Future<List<Map<String, dynamic>>> getUnsyncedLedgerEntries() async {
    final db = await database;
    return db.query('ledger_entries', where: 'synced = 0');
  }

  Future<void> upsertLedgerEntry(Map<String, dynamic> data,
      {bool synced = true}) async {
    final db = await database;
    await db.insert(
      'ledger_entries',
      {...data, 'synced': synced ? 1 : 0},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> markLedgerEntriesSynced(List<String> ids) async {
    final db = await database;
    for (final id in ids) {
      await db.update('ledger_entries', {'synced': 1},
          where: 'id = ?', whereArgs: [id]);
    }
  }

  // --- Customers ---
  Future<void> upsertCustomer(Map<String, dynamic> data,
      {bool synced = true}) async {
    final db = await database;
    await db.insert(
      'customers',
      {...data, 'synced': synced ? 1 : 0},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  // --- Sync metadata ---
  Future<String?> getLastSyncTime() async {
    final db = await database;
    final rows =
        await db.query('sync_meta', where: "key = 'last_sync'");
    if (rows.isEmpty) return null;
    return rows.first['value'] as String;
  }

  Future<void> setLastSyncTime(String timestamp) async {
    final db = await database;
    await db.insert(
      'sync_meta',
      {'key': 'last_sync', 'value': timestamp},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<int> pendingCount() async {
    final db = await database;
    final txnCount = Sqflite.firstIntValue(
        await db.rawQuery('SELECT COUNT(*) FROM transactions WHERE synced = 0'));
    final ledgerCount = Sqflite.firstIntValue(
        await db.rawQuery('SELECT COUNT(*) FROM ledger_entries WHERE synced = 0'));
    return (txnCount ?? 0) + (ledgerCount ?? 0);
  }

  Future<void> close() async {
    final db = _db;
    if (db != null) await db.close();
    _db = null;
  }
}
