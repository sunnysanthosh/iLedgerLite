import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/account_repository.dart';

final accountListProvider =
    FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(accountRepositoryProvider);
  return repo.getAccounts();
});
