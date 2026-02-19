import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

class SpendingChart extends StatelessWidget {
  const SpendingChart({super.key, required this.categories});

  final List<Map<String, dynamic>> categories;

  static const _chartColors = [
    Color(0xFFC62828),
    Color(0xFF1565C0),
    Color(0xFF2E7D32),
    Color(0xFFF57F17),
    Color(0xFF6A1B9A),
    Color(0xFF00838F),
    Color(0xFFD84315),
    Color(0xFF37474F),
  ];

  @override
  Widget build(BuildContext context) {
    final total = categories.fold<double>(
      0,
      (sum, c) => sum + (double.tryParse(c['spent']?.toString() ?? '0') ?? 0),
    );

    if (total == 0) {
      return const SizedBox(
        height: 200,
        child: Center(child: Text('No data')),
      );
    }

    final sections = categories.asMap().entries.map((e) {
      final index = e.key;
      final cat = e.value;
      final spent = double.tryParse(cat['spent']?.toString() ?? '0') ?? 0;
      final pct = (spent / total * 100);
      final color = _chartColors[index % _chartColors.length];

      return PieChartSectionData(
        value: spent,
        title: pct >= 5 ? '${pct.toStringAsFixed(0)}%' : '',
        color: color,
        radius: 50,
        titleStyle: const TextStyle(
            fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white),
      );
    }).toList();

    return SizedBox(
      height: 220,
      child: Row(
        children: [
          Expanded(
            child: PieChart(
              PieChartData(
                sections: sections,
                centerSpaceRadius: 36,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: categories.take(6).toList().asMap().entries.map((e) {
                final index = e.key;
                final cat = e.value;
                final color = _chartColors[index % _chartColors.length];
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    children: [
                      Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                              color: color, shape: BoxShape.circle)),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          cat['category_name'] as String? ?? '',
                          style: const TextStyle(fontSize: 12),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}
