import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../theme/app_colors.dart';

class AmountText extends StatelessWidget {
  const AmountText({
    super.key,
    required this.amount,
    this.type,
    this.currency = 'INR',
    this.fontSize = 16,
    this.fontWeight = FontWeight.w600,
  });

  final String amount;
  final String? type;
  final String currency;
  final double fontSize;
  final FontWeight fontWeight;

  @override
  Widget build(BuildContext context) {
    final value = double.tryParse(amount) ?? 0;
    final formatted = NumberFormat.currency(
      symbol: _currencySymbol(currency),
      decimalDigits: 2,
    ).format(value);

    Color color;
    String prefix = '';
    if (type == 'income') {
      color = AppColors.income;
      prefix = '+';
    } else if (type == 'expense') {
      color = AppColors.expense;
      prefix = '-';
    } else {
      color = Theme.of(context).colorScheme.onSurface;
    }

    return Text(
      '$prefix$formatted',
      style: TextStyle(
        fontSize: fontSize,
        fontWeight: fontWeight,
        color: color,
      ),
    );
  }

  static String _currencySymbol(String code) {
    switch (code.toUpperCase()) {
      case 'INR':
        return '\u20B9';
      case 'USD':
        return '\$';
      case 'EUR':
        return '\u20AC';
      case 'GBP':
        return '\u00A3';
      default:
        return '$code ';
    }
  }
}
