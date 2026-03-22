import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/storage/token_storage.dart';
import '../data/auth_repository.dart';

class AuthState {
  const AuthState({
    this.isLoggedIn = false,
    this.user,
    this.isLoading = false,
    this.error,
    this.organisations = const [],
    this.currentOrgId,
  });

  final bool isLoggedIn;
  final Map<String, dynamic>? user;
  final bool isLoading;
  final String? error;
  final List<Map<String, dynamic>> organisations;
  final String? currentOrgId;

  AuthState copyWith({
    bool? isLoggedIn,
    Map<String, dynamic>? user,
    bool? isLoading,
    String? error,
    List<Map<String, dynamic>>? organisations,
    String? currentOrgId,
  }) =>
      AuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        error: error,
        organisations: organisations ?? this.organisations,
        currentOrgId: currentOrgId ?? this.currentOrgId,
      );
}

final authStateProvider =
    AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final repo = ref.read(authRepositoryProvider);
    final storage = ref.read(tokenStorageProvider);
    final loggedIn = await repo.isLoggedIn();
    if (loggedIn) {
      try {
        final profile = await repo.getProfile();
        final orgs = _parseOrgs(profile);
        final savedOrgId = await storage.getCurrentOrgId();
        final orgId = savedOrgId ?? _defaultOrgId(orgs);
        if (orgId != null) await storage.saveCurrentOrgId(orgId);
        return AuthState(
          isLoggedIn: true,
          user: profile,
          organisations: orgs,
          currentOrgId: orgId,
        );
      } catch (_) {
        await repo.logout();
        return const AuthState();
      }
    }
    return const AuthState();
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      final repo = ref.read(authRepositoryProvider);
      final storage = ref.read(tokenStorageProvider);
      await repo.login(email, password);
      final profile = await repo.getProfile();
      final orgs = _parseOrgs(profile);
      final orgId = _defaultOrgId(orgs);
      if (orgId != null) await storage.saveCurrentOrgId(orgId);
      state = AsyncValue.data(AuthState(
        isLoggedIn: true,
        user: profile,
        organisations: orgs,
        currentOrgId: orgId,
      ));
    } catch (e) {
      state = AsyncValue.data(AuthState(error: _parseError(e)));
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
  }) async {
    state = const AsyncValue.data(AuthState(isLoading: true));
    try {
      final repo = ref.read(authRepositoryProvider);
      final storage = ref.read(tokenStorageProvider);
      await repo.register(
        email: email,
        password: password,
        fullName: fullName,
        phone: phone,
      );
      final profile = await repo.getProfile();
      final orgs = _parseOrgs(profile);
      final orgId = _defaultOrgId(orgs);
      if (orgId != null) await storage.saveCurrentOrgId(orgId);
      state = AsyncValue.data(AuthState(
        isLoggedIn: true,
        user: profile,
        organisations: orgs,
        currentOrgId: orgId,
      ));
    } catch (e) {
      state = AsyncValue.data(AuthState(error: _parseError(e)));
    }
  }

  Future<void> switchOrganisation(String orgId) async {
    final storage = ref.read(tokenStorageProvider);
    await storage.saveCurrentOrgId(orgId);
    final current = state.valueOrNull ?? const AuthState();
    state = AsyncValue.data(current.copyWith(currentOrgId: orgId));
  }

  Future<void> logout() async {
    final repo = ref.read(authRepositoryProvider);
    final storage = ref.read(tokenStorageProvider);
    await repo.logout();
    await storage.clearOrgId();
    state = const AsyncValue.data(AuthState());
  }

  List<Map<String, dynamic>> _parseOrgs(Map<String, dynamic> profile) {
    final raw = profile['organisations'];
    if (raw is List) {
      return raw.cast<Map<String, dynamic>>();
    }
    return const [];
  }

  String? _defaultOrgId(List<Map<String, dynamic>> orgs) {
    if (orgs.isEmpty) return null;
    final personal = orgs.firstWhere(
      (o) => o['is_personal'] == true,
      orElse: () => orgs.first,
    );
    return personal['id'] as String?;
  }

  String _parseError(Object e) {
    if (e is Exception) {
      final msg = e.toString();
      if (msg.contains('401')) return 'Invalid email or password';
      if (msg.contains('409')) return 'Email already registered';
      if (msg.contains('422')) return 'Please check your input';
    }
    return 'Something went wrong. Please try again.';
  }
}
