import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/token_storage.dart';
import 'api_constants.dart';
import 'auth_interceptor.dart';
import 'certificate_pinning.dart';

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

    // Apply certificate pinning when enabled (production builds only).
    // CertificatePinning.init() must be awaited in main() before providers are read.
    if (CertificatePinning.isEnabled && CertificatePinning.context != null) {
      (_dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () =>
          HttpClient(context: CertificatePinning.context!);
    }

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

  Future<Response> getProfitLoss({String? startDate, String? endDate}) =>
      _dio.get('${ApiConstants.reportBase}/reports/profit-loss',
          queryParameters: {
            if (startDate != null) 'start_date': startDate,
            if (endDate != null) 'end_date': endDate,
          });

  Future<Response> getCashflow(
          {String? startDate, String? endDate, String period = 'monthly'}) =>
      _dio.get('${ApiConstants.reportBase}/reports/cashflow',
          queryParameters: {
            if (startDate != null) 'start_date': startDate,
            if (endDate != null) 'end_date': endDate,
            'period': period,
          });

  Future<Response> getBudget({String? startDate, String? endDate}) =>
      _dio.get('${ApiConstants.reportBase}/reports/budget',
          queryParameters: {
            if (startDate != null) 'start_date': startDate,
            if (endDate != null) 'end_date': endDate,
          });

  Future<Response> exportTransactions(
          {String? startDate, String? endDate, String format = 'csv'}) =>
      _dio.get('${ApiConstants.reportBase}/reports/export',
          queryParameters: {
            if (startDate != null) 'start_date': startDate,
            if (endDate != null) 'end_date': endDate,
            'format': format,
          });

  // --- Customers ---
  Future<Response> getCustomers({String? search, int skip = 0, int limit = 20}) =>
      _dio.get('${ApiConstants.ledgerBase}/customers', queryParameters: {
        if (search != null && search.isNotEmpty) 'search': search,
        'skip': skip,
        'limit': limit,
      });

  Future<Response> getCustomer(String id) =>
      _dio.get('${ApiConstants.ledgerBase}/customers/$id');

  Future<Response> createCustomer(Map<String, dynamic> data) =>
      _dio.post('${ApiConstants.ledgerBase}/customers', data: data);

  Future<Response> updateCustomer(String id, Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.ledgerBase}/customers/$id', data: data);

  // --- Ledger Entries ---
  Future<Response> createLedgerEntry(Map<String, dynamic> data) =>
      _dio.post('${ApiConstants.ledgerBase}/ledger-entry', data: data);

  Future<Response> getLedgerHistory(String customerId,
          {int skip = 0, int limit = 20}) =>
      _dio.get('${ApiConstants.ledgerBase}/ledger/$customerId',
          queryParameters: {'skip': skip, 'limit': limit});

  Future<Response> settleLedgerEntry(
          String id, Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.ledgerBase}/ledger-entry/$id', data: data);

  // --- User Profile ---
  Future<Response> getUserProfile() =>
      _dio.get('${ApiConstants.userBase}/users/me');

  Future<Response> updateUserProfile(Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.userBase}/users/me', data: data);

  Future<Response> updateUserSettings(Map<String, dynamic> data) =>
      _dio.put('${ApiConstants.userBase}/users/me/settings', data: data);

  // --- Sync ---
  Future<Response> syncPush(Map<String, dynamic> data) =>
      _dio.post('${ApiConstants.syncBase}/sync/push', data: data);

  Future<Response> syncPull(String deviceId, {String? since}) =>
      _dio.get('${ApiConstants.syncBase}/sync/pull', queryParameters: {
        'device_id': deviceId,
        if (since != null) 'since': since,
      });

  Future<Response> syncStatus(String deviceId) =>
      _dio.get('${ApiConstants.syncBase}/sync/status',
          queryParameters: {'device_id': deviceId});
}
