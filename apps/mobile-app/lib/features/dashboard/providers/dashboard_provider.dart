import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/dashboard_repository.dart';

class DashboardData {
  const DashboardData({
    required this.summary,
    required this.recentTransactions,
  });

  final Map<String, dynamic> summary;
  final List<Map<String, dynamic>> recentTransactions;
}

final dashboardProvider =
    FutureProvider.autoDispose<DashboardData>((ref) async {
  final repo = ref.watch(dashboardRepositoryProvider);
  final results = await Future.wait([
    repo.getSummary(),
    repo.getRecentTransactions(limit: 5),
  ]);
  return DashboardData(
    summary: results[0] as Map<String, dynamic>,
    recentTransactions: results[1] as List<Map<String, dynamic>>,
  );
});
