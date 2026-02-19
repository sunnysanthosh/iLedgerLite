import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';

final settingsRepositoryProvider = Provider<SettingsRepository>((ref) {
  return SettingsRepository(apiClient: ref.watch(apiClientProvider));
});

class SettingsRepository {
  SettingsRepository({required ApiClient apiClient}) : _apiClient = apiClient;

  final ApiClient _apiClient;

  Future<Map<String, dynamic>> getUserProfile() async {
    final response = await _apiClient.getUserProfile();
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateProfile({
    String? fullName,
    String? phone,
    String? businessName,
  }) async {
    final data = <String, dynamic>{};
    if (fullName != null) data['full_name'] = fullName;
    if (phone != null) data['phone'] = phone;
    if (businessName != null) data['business_name'] = businessName;
    final response = await _apiClient.updateUserProfile(data);
    return response.data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> updateSettings({
    String? currency,
    String? language,
    bool? notificationsEnabled,
    bool? emailNotifications,
  }) async {
    final data = <String, dynamic>{};
    if (currency != null) data['currency'] = currency;
    if (language != null) data['language'] = language;
    if (notificationsEnabled != null) {
      data['notifications_enabled'] = notificationsEnabled;
    }
    if (emailNotifications != null) {
      data['email_notifications'] = emailNotifications;
    }
    final response = await _apiClient.updateUserSettings(data);
    return response.data as Map<String, dynamic>;
  }
}
