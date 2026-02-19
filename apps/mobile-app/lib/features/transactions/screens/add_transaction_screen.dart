import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/widgets/loading_overlay.dart';
import '../../accounts/providers/account_provider.dart';
import '../data/transaction_repository.dart';
import '../providers/transaction_provider.dart';

class AddTransactionScreen extends ConsumerStatefulWidget {
  const AddTransactionScreen({super.key});

  @override
  ConsumerState<AddTransactionScreen> createState() =>
      _AddTransactionScreenState();
}

class _AddTransactionScreenState extends ConsumerState<AddTransactionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _descriptionController = TextEditingController();

  String _type = 'expense';
  String? _accountId;
  String? _categoryId;
  DateTime _date = DateTime.now();
  bool _isSubmitting = false;

  @override
  void dispose() {
    _amountController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_accountId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select an account')),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final repo = ref.read(transactionRepositoryProvider);
      await repo.createTransaction(
        accountId: _accountId!,
        type: _type,
        amount: _amountController.text.trim(),
        transactionDate: _date.toUtc().toIso8601String(),
        categoryId: _categoryId,
        description: _descriptionController.text.trim(),
      );
      ref.invalidate(transactionListProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Transaction added')),
        );
        context.go('/transactions');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final accountsAsync = ref.watch(accountListProvider);
    final categoriesAsync = ref.watch(categoriesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Add Transaction')),
      body: LoadingOverlay(
        isLoading: _isSubmitting,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Type selector
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(
                        value: 'income',
                        label: Text('Income'),
                        icon: Icon(Icons.arrow_downward)),
                    ButtonSegment(
                        value: 'expense',
                        label: Text('Expense'),
                        icon: Icon(Icons.arrow_upward)),
                    ButtonSegment(
                        value: 'transfer',
                        label: Text('Transfer'),
                        icon: Icon(Icons.swap_horiz)),
                  ],
                  selected: {_type},
                  onSelectionChanged: (selected) =>
                      setState(() => _type = selected.first),
                ),
                const SizedBox(height: 20),

                // Amount
                TextFormField(
                  controller: _amountController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Amount',
                    prefixText: '\u20B9 ',
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Amount is required';
                    }
                    final amount = double.tryParse(value.trim());
                    if (amount == null || amount <= 0) {
                      return 'Enter a valid positive amount';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),

                // Account dropdown
                accountsAsync.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (_, __) => const Text('Could not load accounts'),
                  data: (accounts) => DropdownButtonFormField<String>(
                    value: _accountId,
                    decoration: const InputDecoration(
                      labelText: 'Account',
                      prefixIcon: Icon(Icons.account_balance_wallet_outlined),
                    ),
                    items: accounts.map<DropdownMenuItem<String>>((a) {
                      return DropdownMenuItem(
                        value: a['id'] as String,
                        child: Text('${a['name']} (${a['type']})'),
                      );
                    }).toList(),
                    onChanged: (value) => setState(() => _accountId = value),
                    validator: (value) =>
                        value == null ? 'Select an account' : null,
                  ),
                ),
                const SizedBox(height: 16),

                // Category dropdown
                categoriesAsync.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (_, __) => const Text('Could not load categories'),
                  data: (categories) {
                    final filtered = categories
                        .where((c) =>
                            c['type'] == _type || _type == 'transfer')
                        .toList();
                    return DropdownButtonFormField<String>(
                      value: _categoryId,
                      decoration: const InputDecoration(
                        labelText: 'Category (optional)',
                        prefixIcon: Icon(Icons.category_outlined),
                      ),
                      items: [
                        const DropdownMenuItem(
                            value: null, child: Text('None')),
                        ...filtered.map<DropdownMenuItem<String>>((c) {
                          return DropdownMenuItem(
                            value: c['id'] as String,
                            child: Text(c['name'] as String),
                          );
                        }),
                      ],
                      onChanged: (value) =>
                          setState(() => _categoryId = value),
                    );
                  },
                ),
                const SizedBox(height: 16),

                // Date
                InkWell(
                  onTap: _pickDate,
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'Date',
                      prefixIcon: Icon(Icons.calendar_today_outlined),
                    ),
                    child: Text(DateFormat('MMMM d, yyyy').format(_date)),
                  ),
                ),
                const SizedBox(height: 16),

                // Description
                TextFormField(
                  controller: _descriptionController,
                  textInputAction: TextInputAction.done,
                  maxLines: 2,
                  decoration: const InputDecoration(
                    labelText: 'Description (optional)',
                    prefixIcon: Icon(Icons.notes_outlined),
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 24),

                ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  child: const Text('Add Transaction'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
