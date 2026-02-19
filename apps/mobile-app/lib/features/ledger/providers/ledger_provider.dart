import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/ledger_repository.dart';

final customerSearchProvider = StateProvider<String>((ref) => '');

final customerListProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repo = ref.watch(ledgerRepositoryProvider);
  final search = ref.watch(customerSearchProvider);
  return repo.getCustomers(
    search: search.isEmpty ? null : search,
    limit: 50,
  );
});

final customerDetailProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, String>((ref, customerId) async {
  final repo = ref.watch(ledgerRepositoryProvider);
  return repo.getCustomer(customerId);
});

final ledgerHistoryProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, String>((ref, customerId) async {
  final repo = ref.watch(ledgerRepositoryProvider);
  return repo.getLedgerHistory(customerId, limit: 100);
});
