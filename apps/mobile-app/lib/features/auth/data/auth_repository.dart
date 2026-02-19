import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/token_storage.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    apiClient: ref.watch(apiClientProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

class AuthRepository {
  AuthRepository({
    required ApiClient apiClient,
    required TokenStorage tokenStorage,
  })  : _apiClient = apiClient,
        _tokenStorage = tokenStorage;

  final ApiClient _apiClient;
  final TokenStorage _tokenStorage;

  Future<void> login(String email, String password) async {
    final response = await _apiClient.login(email, password);
    await _tokenStorage.saveTokens(
      accessToken: response.data['access_token'],
      refreshToken: response.data['refresh_token'],
    );
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
  }) async {
    await _apiClient.register(
      email: email,
      password: password,
      fullName: fullName,
      phone: phone,
    );
    // Auto-login after registration
    await login(email, password);
  }

  Future<Map<String, dynamic>> getProfile() async {
    final response = await _apiClient.getMe();
    return response.data as Map<String, dynamic>;
  }

  Future<void> logout() async {
    await _tokenStorage.clearTokens();
  }

  Future<bool> isLoggedIn() => _tokenStorage.hasTokens();
}
