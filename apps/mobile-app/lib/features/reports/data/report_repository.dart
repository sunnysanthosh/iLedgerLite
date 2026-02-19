import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final reportRepositoryProvider = Provider<ReportRepository>((ref) {
  return ReportRepository(apiClient: ref.watch(apiClientProvider));
});

class ReportRepository {
  ReportRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> getProfitLoss(
      {String? startDate, String? endDate}) async {
    final response =
        await _apiClient.getProfitLoss(startDate: startDate, endDate: endDate);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getCashflow(
      {String? startDate, String? endDate, String period = 'monthly'}) async {
    final response = await _apiClient.getCashflow(
        startDate: startDate, endDate: endDate, period: period);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getBudget(
      {String? startDate, String? endDate}) async {
    final response =
        await _apiClient.getBudget(startDate: startDate, endDate: endDate);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> exportTransactions(
      {String? startDate, String? endDate, String format = 'csv'}) async {
    final response = await _apiClient.exportTransactions(
        startDate: startDate, endDate: endDate, format: format);
    return response.data as Map<String, dynamic>;
  }
}
