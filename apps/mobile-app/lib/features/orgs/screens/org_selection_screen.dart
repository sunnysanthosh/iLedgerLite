import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../auth/providers/auth_provider.dart';

/// Shown when a user belongs to more than one organisation and has not yet
/// selected an active org in this session.
class OrgSelectionScreen extends ConsumerWidget {
  const OrgSelectionScreen({super.key});

  static const roleBadgeColors = {
    'owner': Color(0xFF1E40AF),
    'member': Color(0xFF374151),
    'read_only': Color(0xFF92400E),
  };

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authAsync = ref.watch(authStateProvider);

    return authAsync.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(body: Center(child: Text('Error: $e'))),
      data: (authState) {
        final orgs = authState.organisations;

        return Scaffold(
          appBar: AppBar(
            title: const Text('Select Organisation'),
            automaticallyImplyLeading: false,
          ),
          body: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(16, 20, 16, 8),
                child: Text(
                  'You belong to multiple organisations.\nChoose one to continue.',
                  style: TextStyle(fontSize: 14, color: Colors.black54),
                ),
              ),
              Expanded(
                child: ListView.separated(
                  itemCount: orgs.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final org = orgs[index];
                    final orgId = org['id'] as String;
                    final name = org['name'] as String? ?? orgId;
                    final role = org['role'] as String? ?? 'member';
                    final isPersonal = org['is_personal'] as bool? ?? false;
                    final badgeColor = roleBadgeColors[role] ?? const Color(0xFF374151);

                    return ListTile(
                      title: Text(name, style: const TextStyle(fontWeight: FontWeight.w600)),
                      subtitle: isPersonal ? const Text('Personal') : null,
                      trailing: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: badgeColor.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          role.replaceAll('_', ' '),
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: badgeColor,
                          ),
                        ),
                      ),
                      onTap: () async {
                        await ref.read(authStateProvider.notifier).switchOrganisation(orgId);
                        if (context.mounted) context.go('/dashboard');
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
