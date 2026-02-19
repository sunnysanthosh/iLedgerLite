import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/token_storage.dart';
import 'api_constants.dart';
import 'auth_interceptor.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  return ApiClient(tokenStorage: tokenStorage);
});

class ApiClient {
  ApiClient({required TokenStorage tokenStorage})
      : _tokenStorage = tokenStorage {
    _dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));
    _dio.interceptors.add(AuthInterceptor(
      dio: _dio,
      tokenStorage: _tokenStorage,
    ));
  }

  final TokenStorage _tokenStorage;
  late final Dio _dio;

  // --- Auth ---
  Future<Response> login(String email, String password) => _dio.post(
        '${ApiConstants.authBase}/auth/login',
        data: {'email': email, 'password': password},
      );

  Future<Response> register({
    required String email,
    required String password,
    required String fullName,
    String? phone,
  }) =>
      _dio.post(
        '${ApiConstants.authBase}/auth/register',
        data: {
          'email': email,
          'password': password,
          'full_name': fullName,
          if (phone != null) 'phone': phone,
        },
      );

  Future<Response> refreshToken(String refreshToken) => _dio.post(
        '${ApiConstants.authBase}/auth/refresh',
        data: {'refresh_token': refreshToken},
      );

  Future<Response> getMe() =>
      _dio.get('${ApiConstants.authBase}/auth/me');

  // --- Accounts ---
  Future<Response> getAccounts() =>
      _dio.get('${ApiConstants.transactionBase}/accounts');

  Future<Response> getAccount(String id) =>
      _dio.get('${ApiConstants.transactionBase}/accounts/$id');

  Future<Response> createAccount(Map<String, dynamic> data) =>
      _dio.post('${ApiConstants.transactionBase}/accounts', data: data);

  Future<Response> updateAccount(String id, Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.transactionBase}/accounts/$id', data: data);

  Future<Response> deleteAccount(String id) =>
      _dio.delete('${ApiConstants.transactionBase}/accounts/$id');

  // --- Categories ---
  Future<Response> getCategories({String? type}) => _dio.get(
        '${ApiConstants.transactionBase}/categories',
        queryParameters: {if (type != null) 'type': type},
      );

  // --- Transactions ---
  Future<Response> getTransactions({
    String? accountId,
    String? categoryId,
    String? type,
    String? dateFrom,
    String? dateTo,
    int skip = 0,
    int limit = 20,
  }) =>
      _dio.get(
        '${ApiConstants.transactionBase}/transactions',
        queryParameters: {
          if (accountId != null) 'account_id': accountId,
          if (categoryId != null) 'category_id': categoryId,
          if (type != null) 'type': type,
          if (dateFrom != null) 'date_from': dateFrom,
          if (dateTo != null) 'date_to': dateTo,
          'skip': skip,
          'limit': limit,
        },
      );

  Future<Response> getTransaction(String id) =>
      _dio.get('${ApiConstants.transactionBase}/transactions/$id');

  Future<Response> createTransaction(Map<String, dynamic> data) =>
      _dio.post('${ApiConstants.transactionBase}/transactions', data: data);

  Future<Response> updateTransaction(
          String id, Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.transactionBase}/transactions/$id',
          data: data);

  Future<Response> deleteTransaction(String id) =>
      _dio.delete('${ApiConstants.transactionBase}/transactions/$id');

  // --- Reports ---
  Future<Response> getDashboardSummary() =>
      _dio.get('${ApiConstants.reportBase}/reports/summary');
}
