import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final accountRepositoryProvider = Provider<AccountRepository>((ref) {
  return AccountRepository(apiClient: ref.watch(apiClientProvider));
});

class AccountRepository {
  AccountRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<List<Map<String, dynamic>>> getAccounts() async {
    final response = await _apiClient.getAccounts();
    return (response.data as List).cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> createAccount({
    required String name,
    required String type,
    String currency = 'INR',
  }) async {
    final response = await _apiClient.createAccount({
      'name': name,
      'type': type,
      'currency': currency,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<void> deleteAccount(String id) async {
    await _apiClient.deleteAccount(id);
  }
}
