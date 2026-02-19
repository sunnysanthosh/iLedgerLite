import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/amount_text.dart';

class RecentTransactionTile extends StatelessWidget {
  const RecentTransactionTile({
    super.key,
    required this.transaction,
  });

  final Map<String, dynamic> transaction;

  @override
  Widget build(BuildContext context) {
    final type = transaction['type'] as String? ?? 'expense';
    final description =
        transaction['description'] as String? ?? 'No description';
    final amount = transaction['amount']?.toString() ?? '0.00';
    final dateStr = transaction['transaction_date'] as String?;

    String formattedDate = '';
    if (dateStr != null) {
      final date = DateTime.tryParse(dateStr);
      if (date != null) {
        formattedDate = DateFormat('MMM d').format(date);
      }
    }

    IconData icon;
    Color iconColor;
    switch (type) {
      case 'income':
        icon = Icons.arrow_downward;
        iconColor = AppColors.income;
      case 'transfer':
        icon = Icons.swap_horiz;
        iconColor = AppColors.transfer;
      default:
        icon = Icons.arrow_upward;
        iconColor = AppColors.expense;
    }

    return ListTile(
      leading: CircleAvatar(
        backgroundColor: iconColor.withOpacity(0.1),
        child: Icon(icon, color: iconColor, size: 20),
      ),
      title: Text(
        description,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Text(formattedDate),
      trailing: AmountText(amount: amount, type: type),
      dense: true,
    );
  }
}
