import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/sync/sync_service.dart';
import '../../../core/theme/app_colors.dart';
import '../../../features/auth/providers/auth_provider.dart';
import '../data/settings_repository.dart';
import '../providers/settings_provider.dart';

const _currencyLabels = {
  'INR': 'INR (Indian Rupee)',
  'USD': 'USD (US Dollar)',
  'EUR': 'EUR (Euro)',
  'GBP': 'GBP (British Pound)',
};

const _languageLabels = {
  'en': 'English',
  'hi': 'Hindi',
  'ta': 'Tamil',
  'te': 'Telugu',
};

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(userProfileProvider);
    final syncAsync = ref.watch(syncStatusProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        children: [
          // Profile section
          profileAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (_, __) => const ListTile(
              leading: CircleAvatar(child: Icon(Icons.person)),
              title: Text('Could not load profile'),
            ),
            data: (profile) => _ProfileSection(
              profile: profile,
              onEdit: () => _showProfileEditor(context, ref, profile),
            ),
          ),
          const Divider(),

          // Sync status
          syncAsync.when(
            loading: () => const ListTile(
              leading: Icon(Icons.sync),
              title: Text('Sync'),
              subtitle: Text('Checking...'),
            ),
            error: (_, __) => ListTile(
              leading: const Icon(Icons.sync_problem, color: AppColors.expense),
              title: const Text('Sync'),
              subtitle: const Text('Unable to check sync status'),
              trailing: IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () {
                  final service = ref.read(syncServiceProvider);
                  service.sync();
                },
              ),
            ),
            data: (status) => ListTile(
              leading: Icon(
                status.state == SyncState.syncing
                    ? Icons.sync
                    : status.state == SyncState.error
                        ? Icons.sync_problem
                        : Icons.cloud_done,
                color: status.state == SyncState.error
                    ? AppColors.expense
                    : AppColors.income,
              ),
              title: const Text('Sync'),
              subtitle: Text(
                status.state == SyncState.syncing
                    ? 'Syncing...'
                    : status.pendingCount > 0
                        ? '${status.pendingCount} pending changes'
                        : status.lastSyncTime != null
                            ? 'Last synced: ${_formatTime(status.lastSyncTime!)}'
                            : 'Not yet synced',
              ),
              trailing: IconButton(
                icon: const Icon(Icons.sync),
                onPressed: status.state == SyncState.syncing
                    ? null
                    : () {
                        final service = ref.read(syncServiceProvider);
                        service.sync();
                      },
              ),
            ),
          ),
          const Divider(),

          // Preferences — read current values from profile
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Text('Preferences',
                style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: Colors.grey)),
          ),
          profileAsync.when(
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
            data: (profile) {
              final settings =
                  profile['settings'] as Map<String, dynamic>? ?? {};
              final currency = settings['currency'] as String? ?? 'INR';
              final language = settings['language'] as String? ?? 'en';
              return Column(
                children: [
                  ListTile(
                    leading: const Icon(Icons.currency_rupee),
                    title: const Text('Currency'),
                    subtitle: Text(
                        _currencyLabels[currency] ?? '$currency'),
                    onTap: () =>
                        _showCurrencyPicker(context, ref, currency),
                  ),
                  ListTile(
                    leading: const Icon(Icons.language),
                    title: const Text('Language'),
                    subtitle: Text(
                        _languageLabels[language] ?? language),
                    onTap: () =>
                        _showLanguagePicker(context, ref, language),
                  ),
                ],
              );
            },
          ),
          const Divider(),

          // Notifications — read current values from profile
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Text('Notifications',
                style: TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: Colors.grey)),
          ),
          profileAsync.when(
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
            data: (profile) {
              final settings =
                  profile['settings'] as Map<String, dynamic>? ?? {};
              final pushEnabled =
                  settings['notifications_enabled'] as bool? ?? true;
              final emailEnabled =
                  settings['email_notifications'] as bool? ?? false;
              return Column(
                children: [
                  SwitchListTile(
                    secondary: const Icon(Icons.notifications_outlined),
                    title: const Text('Push Notifications'),
                    value: pushEnabled,
                    onChanged: (val) =>
                        _updateSetting(ref, notificationsEnabled: val),
                  ),
                  SwitchListTile(
                    secondary: const Icon(Icons.email_outlined),
                    title: const Text('Email Notifications'),
                    value: emailEnabled,
                    onChanged: (val) =>
                        _updateSetting(ref, emailNotifications: val),
                  ),
                ],
              );
            },
          ),
          const Divider(),

          // Account actions
          ListTile(
            leading: const Icon(Icons.logout, color: AppColors.expense),
            title:
                const Text('Log Out', style: TextStyle(color: AppColors.expense)),
            onTap: () => _confirmLogout(context, ref),
          ),
          const SizedBox(height: 24),
          Center(
            child: Text(
              'LedgerLite v1.0.0',
              style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  String _formatTime(String isoTime) {
    try {
      final dt = DateTime.parse(isoTime).toLocal();
      final now = DateTime.now();
      final diff = now.difference(dt);
      if (diff.inMinutes < 1) return 'just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      return '${dt.month}/${dt.day} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return isoTime;
    }
  }

  void _showCurrencyPicker(
      BuildContext context, WidgetRef ref, String current) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final entry in _currencyLabels.entries)
              ListTile(
                title: Text(entry.value),
                trailing: entry.key == current
                    ? const Icon(Icons.check, color: AppColors.primary)
                    : null,
                onTap: () {
                  Navigator.pop(ctx);
                  _updateSetting(ref, currency: entry.key);
                },
              ),
          ],
        ),
      ),
    );
  }

  void _showLanguagePicker(
      BuildContext context, WidgetRef ref, String current) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final entry in _languageLabels.entries)
              ListTile(
                title: Text(entry.value),
                trailing: entry.key == current
                    ? const Icon(Icons.check, color: AppColors.primary)
                    : null,
                onTap: () {
                  Navigator.pop(ctx);
                  _updateSetting(ref, language: entry.key);
                },
              ),
          ],
        ),
      ),
    );
  }

  void _showProfileEditor(
      BuildContext context, WidgetRef ref, Map<String, dynamic> profile) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => _ProfileEditSheet(
        profile: profile,
        onSave: (name, phone, businessName) async {
          Navigator.pop(ctx);
          try {
            final repo = ref.read(settingsRepositoryProvider);
            await repo.updateProfile(
              fullName: name,
              phone: phone,
              businessName: businessName,
            );
            ref.invalidate(userProfileProvider);
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Profile updated')));
            }
          } catch (e) {
            if (context.mounted) {
              ScaffoldMessenger.of(context)
                  .showSnackBar(SnackBar(content: Text('Error: $e')));
            }
          }
        },
      ),
    );
  }

  Future<void> _updateSetting(
    WidgetRef ref, {
    String? currency,
    String? language,
    bool? notificationsEnabled,
    bool? emailNotifications,
  }) async {
    try {
      final repo = ref.read(settingsRepositoryProvider);
      await repo.updateSettings(
        currency: currency,
        language: language,
        notificationsEnabled: notificationsEnabled,
        emailNotifications: emailNotifications,
      );
      ref.invalidate(userProfileProvider);
    } catch (_) {}
  }

  void _confirmLogout(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Log Out'),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              ref.read(authStateProvider.notifier).logout();
            },
            child: const Text('Log Out',
                style: TextStyle(color: AppColors.expense)),
          ),
        ],
      ),
    );
  }
}

class _ProfileSection extends StatelessWidget {
  const _ProfileSection({required this.profile, required this.onEdit});

  final Map<String, dynamic> profile;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) {
    final name = profile['full_name'] as String? ?? 'User';
    final email = profile['email'] as String? ?? '';
    final phone = profile['phone'] as String? ?? '';
    final initials = name.isNotEmpty
        ? name.split(' ').map((w) => w.isNotEmpty ? w[0] : '').take(2).join()
        : '?';

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: AppColors.primary.withOpacity(0.1),
            child: Text(initials.toUpperCase(),
                style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary)),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name,
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w600)),
                if (email.isNotEmpty)
                  Text(email,
                      style:
                          TextStyle(color: Colors.grey.shade600, fontSize: 14)),
                if (phone.isNotEmpty)
                  Text(phone,
                      style:
                          TextStyle(color: Colors.grey.shade600, fontSize: 13)),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.edit_outlined),
            onPressed: onEdit,
          ),
        ],
      ),
    );
  }
}

class _ProfileEditSheet extends StatefulWidget {
  const _ProfileEditSheet({required this.profile, required this.onSave});

  final Map<String, dynamic> profile;
  final Future<void> Function(String name, String phone, String businessName)
      onSave;

  @override
  State<_ProfileEditSheet> createState() => _ProfileEditSheetState();
}

class _ProfileEditSheetState extends State<_ProfileEditSheet> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _phoneCtrl;
  late final TextEditingController _businessCtrl;
  final _formKey = GlobalKey<FormState>();
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _nameCtrl =
        TextEditingController(text: widget.profile['full_name'] as String? ?? '');
    _phoneCtrl =
        TextEditingController(text: widget.profile['phone'] as String? ?? '');
    _businessCtrl = TextEditingController(
        text: widget.profile['business_name'] as String? ?? '');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _phoneCtrl.dispose();
    _businessCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Edit Profile',
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w600)),
            const SizedBox(height: 20),
            TextFormField(
              controller: _nameCtrl,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                border: OutlineInputBorder(),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Name is required' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _phoneCtrl,
              decoration: const InputDecoration(
                labelText: 'Phone',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _businessCtrl,
              decoration: const InputDecoration(
                labelText: 'Business Name (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _saving
                  ? null
                  : () async {
                      if (!_formKey.currentState!.validate()) return;
                      setState(() => _saving = true);
                      await widget.onSave(
                        _nameCtrl.text.trim(),
                        _phoneCtrl.text.trim(),
                        _businessCtrl.text.trim(),
                      );
                    },
              child: _saving
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }
}
