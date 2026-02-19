import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/auth_repository.dart';

class AuthState {
  const AuthState({
    this.isLoggedIn = false,
    this.user,
    this.isLoading = false,
    this.error,
  });

  final bool isLoggedIn;
  final Map<String, dynamic>? user;
  final bool isLoading;
  final String? error;

  AuthState copyWith({
    bool? isLoggedIn,
    Map<String, dynamic>? user,
    bool? isLoading,
    String? error,
  }) =>
      AuthState(
        isLoggedIn: isLoggedIn ?? this.isLoggedIn,
        user: user ?? this.user,
        isLoading: isLoading ?? this.isLoading,
        error: error,
      );
}

final authStateProvider =
    AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final repo = ref.read(authRepositoryProvider);
    final loggedIn = await repo.isLoggedIn();
    if (loggedIn) {
      try {
        final profile = await repo.getProfile();
        return AuthState(isLoggedIn: true, user: profile);
      } catch (_) {
        await repo.logout();
        return const AuthState();
      }
    }
    return const AuthState();
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.data(
        AuthState(isLoading: true));
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.login(email, password);
      final profile = await repo.getProfile();
      state = AsyncValue.data(
          AuthState(isLoggedIn: true, user: profile));
    } catch (e) {
      state = AsyncValue.data(
          AuthState(error: _parseError(e)));
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
  }) async {
    state = const AsyncValue.data(
        AuthState(isLoading: true));
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.register(
        email: email,
        password: password,
        fullName: fullName,
        phone: phone,
      );
      final profile = await repo.getProfile();
      state = AsyncValue.data(
          AuthState(isLoggedIn: true, user: profile));
    } catch (e) {
      state = AsyncValue.data(
          AuthState(error: _parseError(e)));
    }
  }

  Future<void> logout() async {
    final repo = ref.read(authRepositoryProvider);
    await repo.logout();
    state = const AsyncValue.data(AuthState());
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
