import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/transaction_repository.dart';

// Filter state
class TransactionFilter {
  const TransactionFilter({
    this.accountId,
    this.categoryId,
    this.type,
  });

  final String? accountId;
  final String? categoryId;
  final String? type;
}

final transactionFilterProvider =
    StateProvider<TransactionFilter>((ref) => const TransactionFilter());

// Transaction list
final transactionListProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repo = ref.watch(transactionRepositoryProvider);
  final filter = ref.watch(transactionFilterProvider);
  return repo.getTransactions(
    accountId: filter.accountId,
    categoryId: filter.categoryId,
    type: filter.type,
    limit: 50,
  );
});

// Categories
final categoriesProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(transactionRepositoryProvider);
  return repo.getCategories();
});
