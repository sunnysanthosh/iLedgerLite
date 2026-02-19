import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/amount_text.dart';
import '../providers/report_provider.dart';
import '../widgets/spending_chart.dart';
import '../data/report_repository.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plAsync = ref.watch(profitLossProvider);
    final budgetAsync = ref.watch(budgetProvider);
    final mode = ref.watch(reportModeProvider);
    final startDate = ref.watch(reportStartDateProvider);
    final endDate = ref.watch(reportEndDateProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Reports'),
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            tooltip: 'Export',
            onPressed: () => _showExportOptions(ref, context),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(profitLossProvider);
          ref.invalidate(budgetProvider);
        },
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Date range picker
            _DateRangeBar(
              startDate: startDate,
              endDate: endDate,
              onPick: () => _pickDateRange(context, ref),
              onClear: () {
                ref.read(reportStartDateProvider.notifier).state = null;
                ref.read(reportEndDateProvider.notifier).state = null;
              },
            ),
            const SizedBox(height: 12),

            // Mode toggle
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(
                    value: 'personal',
                    label: Text('Personal'),
                    icon: Icon(Icons.person_outline)),
                ButtonSegment(
                    value: 'business',
                    label: Text('Business'),
                    icon: Icon(Icons.business_outlined)),
              ],
              selected: {mode},
              onSelectionChanged: (v) =>
                  ref.read(reportModeProvider.notifier).state = v.first,
            ),
            const SizedBox(height: 16),

            // P&L card
            plAsync.when(
              loading: () => const Card(
                  child: Padding(
                      padding: EdgeInsets.all(32),
                      child: Center(child: CircularProgressIndicator()))),
              error: (_, __) => const Card(
                  child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Could not load P&L data'))),
              data: (pl) => _ProfitLossCard(data: pl, mode: mode),
            ),
            const SizedBox(height: 16),

            // Spending breakdown
            Text('Spending by Category',
                style: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 12),
            budgetAsync.when(
              loading: () => const SizedBox(
                  height: 200,
                  child: Center(child: CircularProgressIndicator())),
              error: (_, __) => const SizedBox(
                  height: 200,
                  child: Center(child: Text('Could not load budget data'))),
              data: (budget) {
                final categories = (budget['categories'] as List?)
                        ?.cast<Map<String, dynamic>>() ??
                    [];
                if (categories.isEmpty) {
                  return SizedBox(
                    height: 200,
                    child: Center(
                      child: Text('No expense data this period',
                          style: TextStyle(color: Colors.grey.shade500)),
                    ),
                  );
                }
                return SpendingChart(categories: categories);
              },
            ),
            const SizedBox(height: 16),

            // Category list
            budgetAsync.when(
              loading: () => const SizedBox.shrink(),
              error: (_, __) => const SizedBox.shrink(),
              data: (budget) {
                final categories = (budget['categories'] as List?)
                        ?.cast<Map<String, dynamic>>() ??
                    [];
                return Column(
                  children: categories.map((cat) {
                    final name = cat['category_name'] as String? ?? 'Other';
                    final spent = cat['spent']?.toString() ?? '0.00';
                    final count = cat['transaction_count'] as int? ?? 0;
                    return ListTile(
                      dense: true,
                      leading: CircleAvatar(
                        radius: 16,
                        backgroundColor: AppColors.expense.withOpacity(0.1),
                        child: const Icon(Icons.category,
                            size: 16, color: AppColors.expense),
                      ),
                      title: Text(name),
                      subtitle: Text('$count transaction${count == 1 ? '' : 's'}'),
                      trailing: AmountText(
                          amount: spent, type: 'expense', fontSize: 14),
                    );
                  }).toList(),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickDateRange(BuildContext context, WidgetRef ref) async {
    final now = DateTime.now();
    final firstDay = DateTime(now.year - 2);
    final picked = await showDateRangePicker(
      context: context,
      firstDate: firstDay,
      lastDate: now,
      initialDateRange: DateTimeRange(
        start: DateTime(now.year, now.month, 1),
        end: now,
      ),
    );
    if (picked != null) {
      final fmt = DateFormat('yyyy-MM-dd');
      ref.read(reportStartDateProvider.notifier).state =
          fmt.format(picked.start);
      ref.read(reportEndDateProvider.notifier).state = fmt.format(picked.end);
    }
  }

  void _showExportOptions(WidgetRef ref, BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.table_chart),
              title: const Text('Export as CSV'),
              onTap: () {
                Navigator.pop(ctx);
                _export(ref, context, 'csv');
              },
            ),
            ListTile(
              leading: const Icon(Icons.picture_as_pdf),
              title: const Text('Export as PDF'),
              onTap: () {
                Navigator.pop(ctx);
                _export(ref, context, 'pdf');
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _export(
      WidgetRef ref, BuildContext context, String format) async {
    try {
      final repo = ref.read(reportRepositoryProvider);
      final start = ref.read(reportStartDateProvider);
      final end = ref.read(reportEndDateProvider);
      final result = await repo.exportTransactions(
          startDate: start, endDate: end, format: format);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(
                  'Exported ${result['filename'] ?? 'transactions.$format'}')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Export failed: $e')));
      }
    }
  }
}

class _DateRangeBar extends StatelessWidget {
  const _DateRangeBar({
    required this.startDate,
    required this.endDate,
    required this.onPick,
    required this.onClear,
  });

  final String? startDate;
  final String? endDate;
  final VoidCallback onPick;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final hasRange = startDate != null && endDate != null;
    return InkWell(
      onTap: onPick,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.date_range, size: 20, color: AppColors.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                hasRange ? '$startDate  to  $endDate' : 'All time (tap to filter)',
                style: TextStyle(
                  color: hasRange ? Colors.black87 : Colors.grey.shade600,
                  fontSize: 14,
                ),
              ),
            ),
            if (hasRange)
              GestureDetector(
                onTap: onClear,
                child: const Icon(Icons.close, size: 18, color: Colors.grey),
              ),
          ],
        ),
      ),
    );
  }
}

class _ProfitLossCard extends StatelessWidget {
  const _ProfitLossCard({required this.data, required this.mode});

  final Map<String, dynamic> data;
  final String mode;

  @override
  Widget build(BuildContext context) {
    final income = data['total_income']?.toString() ?? '0.00';
    final expenses = data['total_expenses']?.toString() ?? '0.00';
    final netProfit = data['net_profit']?.toString() ?? '0.00';
    final isProfit = (double.tryParse(netProfit) ?? 0) >= 0;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  mode == 'business' ? 'Business P&L' : 'Profit & Loss',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w600),
                ),
                const Spacer(),
                if (mode == 'business')
                  Icon(Icons.business, size: 18, color: Colors.grey.shade500),
              ],
            ),
            Text(
              '${data['start_date'] ?? ''} — ${data['end_date'] ?? ''}',
              style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                    child: _PlItem(
                        label: mode == 'business' ? 'Revenue' : 'Income',
                        amount: income,
                        color: AppColors.income)),
                Expanded(
                    child: _PlItem(
                        label: 'Expenses',
                        amount: expenses,
                        color: AppColors.expense)),
                Expanded(
                    child: _PlItem(
                        label: 'Net Profit',
                        amount: netProfit,
                        color: isProfit
                            ? AppColors.income
                            : AppColors.expense)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _PlItem extends StatelessWidget {
  const _PlItem({
    required this.label,
    required this.amount,
    required this.color,
  });

  final String label;
  final String amount;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(label,
            style: Theme.of(context)
                .textTheme
                .bodySmall
                ?.copyWith(color: Colors.grey)),
        const SizedBox(height: 4),
        Text('\u20B9$amount',
            style: TextStyle(
                color: color, fontWeight: FontWeight.w600, fontSize: 15)),
      ],
    );
  }
}
