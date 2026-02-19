import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/amount_text.dart';
import '../providers/account_provider.dart';

class AccountListScreen extends ConsumerWidget {
  const AccountListScreen({super.key});

  IconData _accountIcon(String type) {
    switch (type) {
      case 'bank':
        return Icons.account_balance;
      case 'cash':
        return Icons.payments;
      case 'credit_card':
        return Icons.credit_card;
      case 'wallet':
        return Icons.account_balance_wallet;
      case 'loan':
        return Icons.request_quote;
      default:
        return Icons.account_balance_wallet;
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final accountsAsync = ref.watch(accountListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Accounts')),
      body: accountsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.grey),
              const SizedBox(height: 16),
              const Text('Could not load accounts'),
              TextButton(
                onPressed: () => ref.invalidate(accountListProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (accounts) {
          if (accounts.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.account_balance_wallet_outlined,
                      size: 64, color: Colors.grey.shade300),
                  const SizedBox(height: 16),
                  Text(
                    'No accounts yet',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: () => context.go('/accounts/add'),
                    icon: const Icon(Icons.add),
                    label: const Text('Add Account'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(accountListProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: accounts.length,
              itemBuilder: (context, index) {
                final account = accounts[index];
                final type = account['type'] as String? ?? 'cash';
                final balance = account['balance']?.toString() ?? '0.00';

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 8),
                    leading: CircleAvatar(
                      backgroundColor:
                          AppColors.primary.withOpacity(0.1),
                      child: Icon(_accountIcon(type),
                          color: AppColors.primary),
                    ),
                    title: Text(
                      account['name'] as String? ?? 'Account',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      '${type.replaceAll('_', ' ')} \u2022 ${account['currency'] ?? 'INR'}',
                      style: TextStyle(color: Colors.grey.shade600),
                    ),
                    trailing: AmountText(
                      amount: balance,
                      fontSize: 18,
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/accounts/add'),
        child: const Icon(Icons.add),
      ),
    );
  }
}
