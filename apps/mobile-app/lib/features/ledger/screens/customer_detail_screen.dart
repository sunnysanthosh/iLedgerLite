import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/amount_text.dart';
import '../providers/ledger_provider.dart';

class CustomerDetailScreen extends ConsumerWidget {
  const CustomerDetailScreen({super.key, required this.customerId});

  final String customerId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final customerAsync = ref.watch(customerDetailProvider(customerId));
    final historyAsync = ref.watch(ledgerHistoryProvider(customerId));

    return Scaffold(
      appBar: AppBar(
        title: customerAsync.when(
          loading: () => const Text('Customer'),
          error: (_, __) => const Text('Customer'),
          data: (c) => Text(c['name'] as String? ?? 'Customer'),
        ),
      ),
      body: historyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 16),
              const Text('Could not load ledger history'),
              TextButton(
                onPressed: () {
                  ref.invalidate(ledgerHistoryProvider(customerId));
                  ref.invalidate(customerDetailProvider(customerId));
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (data) {
          final totalDebit = data['total_debit']?.toString() ?? '0.00';
          final totalCredit = data['total_credit']?.toString() ?? '0.00';
          final outstanding =
              data['outstanding_balance']?.toString() ?? '0.00';
          final entries = (data['entries'] as List?)
                  ?.cast<Map<String, dynamic>>() ??
              [];

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(ledgerHistoryProvider(customerId));
              ref.invalidate(customerDetailProvider(customerId));
            },
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Summary card
                Card(
                  color: AppColors.primary,
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        Text('Outstanding Balance',
                            style: Theme.of(context)
                                .textTheme
                                .bodyMedium
                                ?.copyWith(color: Colors.white70)),
                        const SizedBox(height: 8),
                        AmountText(
                          amount: outstanding,
                          fontSize: 28,
                          fontWeight: FontWeight.bold,
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                          children: [
                            _SummaryChip(
                                label: 'Total Debit',
                                amount: totalDebit,
                                color: Colors.redAccent.shade100),
                            _SummaryChip(
                                label: 'Total Credit',
                                amount: totalCredit,
                                color: Colors.greenAccent),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Action buttons
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => context.go(
                            '/ledger/customer/$customerId/add-entry?type=debit'),
                        icon: const Icon(Icons.arrow_upward,
                            color: AppColors.expense),
                        label: const Text('Add Debit'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => context.go(
                            '/ledger/customer/$customerId/add-entry?type=credit'),
                        icon: const Icon(Icons.arrow_downward,
                            color: AppColors.income),
                        label: const Text('Add Credit'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // History
                Text('Credit History',
                    style: Theme.of(context)
                        .textTheme
                        .titleMedium
                        ?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 8),

                if (entries.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 32),
                    child: Center(
                      child: Text('No entries yet',
                          style: TextStyle(color: Colors.grey.shade500)),
                    ),
                  )
                else
                  ...entries.map((entry) => _LedgerEntryTile(
                        entry: entry,
                        onSettle: () => _settleEntry(ref, context, entry),
                      )),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () =>
            context.go('/ledger/customer/$customerId/add-entry?type=debit'),
        child: const Icon(Icons.add),
      ),
    );
  }

  Future<void> _settleEntry(
      WidgetRef ref, BuildContext context, Map<String, dynamic> entry) async {
    final entryAmount = entry['amount']?.toString() ?? '0.00';
    final result = await showDialog<_SettleResult>(
      context: context,
      builder: (context) => _SettleDialog(
        type: entry['type'] as String? ?? 'debit',
        amount: entryAmount,
      ),
    );
    if (result == null) return;

    try {
      final repo = ref.read(ledgerRepositoryProvider);
      await repo.settleLedgerEntry(
        entry['id'] as String,
        amount: result.isPartial ? result.partialAmount : null,
      );
      ref.invalidate(ledgerHistoryProvider(customerId));
      ref.invalidate(customerDetailProvider(customerId));
      ref.invalidate(customerListProvider);
      if (context.mounted) {
        final msg = result.isPartial
            ? 'Partial payment of \u20B9${result.partialAmount} recorded'
            : 'Entry settled';
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(msg)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
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
                ?.copyWith(color: Colors.white60)),
        const SizedBox(height: 4),
        Text('\u20B9$amount',
            style: TextStyle(
                color: color, fontWeight: FontWeight.w600, fontSize: 16)),
      ],
    );
  }
}

class _LedgerEntryTile extends StatelessWidget {
  const _LedgerEntryTile({required this.entry, required this.onSettle});

  final Map<String, dynamic> entry;
  final VoidCallback onSettle;

  @override
  Widget build(BuildContext context) {
    final type = entry['type'] as String? ?? 'debit';
    final amount = entry['amount']?.toString() ?? '0.00';
    final description = entry['description'] as String? ?? 'No description';
    final isSettled = entry['is_settled'] as bool? ?? false;
    final dateStr = entry['created_at'] as String?;
    final dueDateStr = entry['due_date'] as String?;

    String formattedDate = '';
    if (dateStr != null) {
      final date = DateTime.tryParse(dateStr);
      if (date != null) formattedDate = DateFormat('MMM d, yyyy').format(date);
    }

    String? dueDateText;
    if (dueDateStr != null) {
      final dueDate = DateTime.tryParse(dueDateStr);
      if (dueDate != null) {
        dueDateText = 'Due: ${DateFormat('MMM d').format(dueDate)}';
      }
    }

    final isDebit = type == 'debit';

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isDebit
              ? AppColors.expense.withOpacity(0.1)
              : AppColors.income.withOpacity(0.1),
          child: Icon(
            isDebit ? Icons.arrow_upward : Icons.arrow_downward,
            color: isDebit ? AppColors.expense : AppColors.income,
            size: 20,
          ),
        ),
        title: Text(description, maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(
          [formattedDate, if (dueDateText != null) dueDateText]
              .join(' \u2022 '),
          style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            AmountText(
              amount: amount,
              type: isDebit ? 'expense' : 'income',
              fontSize: 14,
            ),
            if (isSettled)
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.income.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text('Settled',
                    style: TextStyle(
                        fontSize: 10, color: AppColors.income)),
              )
            else
              GestureDetector(
                onTap: onSettle,
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.warning.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text('Tap to settle',
                      style: TextStyle(
                          fontSize: 10, color: AppColors.warning)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _SettleResult {
  const _SettleResult({this.isPartial = false, this.partialAmount});
  final bool isPartial;
  final String? partialAmount;
}

class _SettleDialog extends StatefulWidget {
  const _SettleDialog({required this.type, required this.amount});
  final String type;
  final String amount;

  @override
  State<_SettleDialog> createState() => _SettleDialogState();
}

class _SettleDialogState extends State<_SettleDialog> {
  bool _isPartial = false;
  final _amountController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Settle Entry'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${widget.type} of \u20B9${widget.amount}'),
            const SizedBox(height: 16),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('Full')),
                ButtonSegment(value: true, label: Text('Partial')),
              ],
              selected: {_isPartial},
              onSelectionChanged: (v) => setState(() => _isPartial = v.first),
            ),
            if (_isPartial) ...[
              const SizedBox(height: 16),
              TextFormField(
                controller: _amountController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Payment amount',
                  prefixText: '\u20B9 ',
                  border: OutlineInputBorder(),
                ),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Enter an amount';
                  final val = double.tryParse(v);
                  if (val == null || val <= 0) return 'Enter a valid amount';
                  final max = double.tryParse(widget.amount) ?? 0;
                  if (val > max) return 'Cannot exceed \u20B9${widget.amount}';
                  return null;
                },
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel')),
        ElevatedButton(
          onPressed: () {
            if (_isPartial && !_formKey.currentState!.validate()) return;
            Navigator.pop(
              context,
              _SettleResult(
                isPartial: _isPartial,
                partialAmount:
                    _isPartial ? _amountController.text.trim() : null,
              ),
            );
          },
          child: Text(_isPartial ? 'Record Payment' : 'Settle Full'),
        ),
      ],
    );
  }
}
