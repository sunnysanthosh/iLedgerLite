import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/amount_text.dart';
import '../providers/ledger_provider.dart';

class CustomerListScreen extends ConsumerStatefulWidget {
  const CustomerListScreen({super.key});

  @override
  ConsumerState<CustomerListScreen> createState() => _CustomerListScreenState();
}

class _CustomerListScreenState extends ConsumerState<CustomerListScreen> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final customersAsync = ref.watch(customerListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Customers'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search by name, phone, or email',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          ref.read(customerSearchProvider.notifier).state = '';
                        },
                      )
                    : null,
              ),
              onChanged: (value) {
                ref.read(customerSearchProvider.notifier).state = value;
              },
            ),
          ),
          Expanded(
            child: customersAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error_outline, size: 48, color: Colors.grey),
                    const SizedBox(height: 16),
                    const Text('Could not load customers'),
                    TextButton(
                      onPressed: () => ref.invalidate(customerListProvider),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
              data: (data) {
                final items = (data['items'] as List?)
                        ?.cast<Map<String, dynamic>>() ??
                    [];

                if (items.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.people_outline,
                            size: 64, color: Colors.grey.shade300),
                        const SizedBox(height: 16),
                        Text('No customers yet',
                            style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 8),
                        ElevatedButton.icon(
                          onPressed: () => context.go('/ledger/add-customer'),
                          icon: const Icon(Icons.person_add),
                          label: const Text('Add Customer'),
                        ),
                      ],
                    ),
                  );
                }

                return RefreshIndicator(
                  onRefresh: () async => ref.invalidate(customerListProvider),
                  child: ListView.builder(
                    itemCount: items.length,
                    itemBuilder: (context, index) {
                      final customer = items[index];
                      final balance =
                          customer['outstanding_balance']?.toString() ?? '0.00';
                      final hasBalance =
                          double.tryParse(balance) != null &&
                              double.parse(balance) > 0;

                      return ListTile(
                        leading: CircleAvatar(
                          backgroundColor: hasBalance
                              ? AppColors.warning.withOpacity(0.1)
                              : AppColors.income.withOpacity(0.1),
                          child: Icon(
                            Icons.person,
                            color: hasBalance
                                ? AppColors.warning
                                : AppColors.income,
                          ),
                        ),
                        title: Text(
                          customer['name'] as String? ?? '',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        subtitle: Text(
                          customer['phone'] as String? ??
                              customer['email'] as String? ??
                              'No contact info',
                          style: TextStyle(color: Colors.grey.shade600),
                        ),
                        trailing: hasBalance
                            ? AmountText(
                                amount: balance,
                                type: 'expense',
                                fontSize: 15,
                              )
                            : Text('Settled',
                                style: TextStyle(
                                    color: AppColors.income, fontSize: 13)),
                        onTap: () => context.go(
                            '/ledger/customer/${customer['id']}'),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/ledger/add-customer'),
        child: const Icon(Icons.person_add),
      ),
    );
  }
}
