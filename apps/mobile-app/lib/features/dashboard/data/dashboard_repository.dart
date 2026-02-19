import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository(apiClient: ref.watch(apiClientProvider));
});

class DashboardRepository {
  DashboardRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> getSummary() async {
    final response = await _apiClient.getDashboardSummary();
    return response.data as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getRecentTransactions({
    int limit = 5,
  }) async {
    final response = await _apiClient.getTransactions(limit: limit);
    final data = response.data as Map<String, dynamic>;
    return (data['items'] as List).cast<Map<String, dynamic>>();
  }
}
