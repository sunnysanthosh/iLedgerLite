import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final transactionRepositoryProvider = Provider<TransactionRepository>((ref) {
  return TransactionRepository(apiClient: ref.watch(apiClientProvider));
});

class TransactionRepository {
  TransactionRepository({required ApiClient apiClient})
      : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> getTransactions({
    String? accountId,
    String? categoryId,
    String? type,
    String? dateFrom,
    String? dateTo,
    int skip = 0,
    int limit = 20,
  }) async {
    final response = await _apiClient.getTransactions(
      accountId: accountId,
      categoryId: categoryId,
      type: type,
      dateFrom: dateFrom,
      dateTo: dateTo,
      skip: skip,
      limit: limit,
    );
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createTransaction({
    required String accountId,
    required String type,
    required String amount,
    required String transactionDate,
    String? categoryId,
    String? description,
  }) async {
    final response = await _apiClient.createTransaction({
      'account_id': accountId,
      'type': type,
      'amount': amount,
      'transaction_date': transactionDate,
      if (categoryId != null) 'category_id': categoryId,
      if (description != null && description.isNotEmpty)
        'description': description,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteTransaction(String id) async {
    await _apiClient.deleteTransaction(id);
  }

  Future<List<Map<String, dynamic>>> getCategories({String? type}) async {
    final response = await _apiClient.getCategories(type: type);
    return (response.data as List).cast<Map<String, dynamic>>();
  }
}
