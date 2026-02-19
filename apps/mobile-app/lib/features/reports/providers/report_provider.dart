import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/report_repository.dart';

/// Selected date range for reports. Null means "all time / server default".
final reportStartDateProvider = StateProvider<String?>((ref) => null);
final reportEndDateProvider = StateProvider<String?>((ref) => null);

/// Report mode: 'personal' or 'business'
final reportModeProvider = StateProvider<String>((ref) => 'personal');

final profitLossProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repo = ref.watch(reportRepositoryProvider);
  final start = ref.watch(reportStartDateProvider);
  final end = ref.watch(reportEndDateProvider);
  return repo.getProfitLoss(startDate: start, endDate: end);
});

final budgetProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repo = ref.watch(reportRepositoryProvider);
  final start = ref.watch(reportStartDateProvider);
  final end = ref.watch(reportEndDateProvider);
  return repo.getBudget(startDate: start, endDate: end);
});
