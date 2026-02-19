import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/loading_overlay.dart';
import '../data/account_repository.dart';
import '../providers/account_provider.dart';

class AddAccountScreen extends ConsumerStatefulWidget {
  const AddAccountScreen({super.key});

  @override
  ConsumerState<AddAccountScreen> createState() => _AddAccountScreenState();
}

class _AddAccountScreenState extends ConsumerState<AddAccountScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  String _type = 'cash';
  String _currency = 'INR';
  bool _isSubmitting = false;

  static const _accountTypes = [
    ('cash', 'Cash', Icons.payments),
    ('bank', 'Bank Account', Icons.account_balance),
    ('credit_card', 'Credit Card', Icons.credit_card),
    ('wallet', 'Digital Wallet', Icons.account_balance_wallet),
    ('loan', 'Loan', Icons.request_quote),
  ];

  static const _currencies = ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'MYR'];

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);
    try {
      final repo = ref.read(accountRepositoryProvider);
      await repo.createAccount(
        name: _nameController.text.trim(),
        type: _type,
        currency: _currency,
      );
      ref.invalidate(accountListProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Account created')),
        );
        context.go('/accounts');
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
    return Scaffold(
      appBar: AppBar(title: const Text('Add Account')),
      body: LoadingOverlay(
        isLoading: _isSubmitting,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _nameController,
                  textInputAction: TextInputAction.next,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Account Name',
                    prefixIcon: Icon(Icons.label_outlined),
                    hintText: 'e.g. Savings, Wallet, Cash',
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Account name is required';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 20),

                // Account type
                Text(
                  'Account Type',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _accountTypes.map((t) {
                    final (value, label, icon) = t;
                    final selected = _type == value;
                    return ChoiceChip(
                      avatar: Icon(icon, size: 18),
                      label: Text(label),
                      selected: selected,
                      onSelected: (_) => setState(() => _type = value),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),

                // Currency
                DropdownButtonFormField<String>(
                  value: _currency,
                  decoration: const InputDecoration(
                    labelText: 'Currency',
                    prefixIcon: Icon(Icons.currency_exchange),
                  ),
                  items: _currencies
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (value) {
                    if (value != null) setState(() => _currency = value);
                  },
                ),
                const SizedBox(height: 32),

                ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  child: const Text('Create Account'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
