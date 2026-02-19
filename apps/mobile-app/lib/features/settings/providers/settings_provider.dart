import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/settings_repository.dart';

final userProfileProvider =
    FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repo = ref.watch(settingsRepositoryProvider);
  return repo.getUserProfile();
});
