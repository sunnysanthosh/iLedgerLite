import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final ledgerRepositoryProvider = Provider<LedgerRepository>((ref) {
  return LedgerRepository(apiClient: ref.watch(apiClientProvider));
});

class LedgerRepository {
  LedgerRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> getCustomers({
    String? search,
    int skip = 0,
    int limit = 20,
  }) async {
    final response = await _apiClient.getCustomers(
        search: search, skip: skip, limit: limit);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getCustomer(String id) async {
    final response = await _apiClient.getCustomer(id);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createCustomer({
    required String name,
    String? phone,
    String? email,
    String? address,
  }) async {
    final response = await _apiClient.createCustomer({
      'name': name,
      if (phone != null && phone.isNotEmpty) 'phone': phone,
      if (email != null && email.isNotEmpty) 'email': email,
      if (address != null && address.isNotEmpty) 'address': address,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getLedgerHistory(String customerId,
      {int skip = 0, int limit = 50}) async {
    final response = await _apiClient.getLedgerHistory(customerId,
        skip: skip, limit: limit);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> createLedgerEntry({
    required String customerId,
    required String amount,
    required String type,
    String? description,
    String? dueDate,
  }) async {
    final response = await _apiClient.createLedgerEntry({
      'customer_id': customerId,
      'amount': amount,
      'type': type,
      if (description != null && description.isNotEmpty)
        'description': description,
      if (dueDate != null) 'due_date': dueDate,
    });
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> settleLedgerEntry(String id,
      {bool isSettled = true, String? amount}) async {
    final response = await _apiClient.settleLedgerEntry(id, {
      'is_settled': isSettled,
      if (amount != null) 'amount': amount,
    });
    return response.data as Map<String, dynamic>;
  }
}
