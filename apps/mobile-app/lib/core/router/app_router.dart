import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/providers/auth_provider.dart';
import '../../features/auth/screens/login_screen.dart';
import '../../features/auth/screens/register_screen.dart';
import '../../features/dashboard/screens/dashboard_screen.dart';
import '../../features/transactions/screens/add_transaction_screen.dart';
import '../../features/transactions/screens/transaction_list_screen.dart';
import '../../features/accounts/screens/account_list_screen.dart';
import '../../features/accounts/screens/add_account_screen.dart';
import '../../features/ledger/screens/customer_list_screen.dart';
import '../../features/ledger/screens/customer_detail_screen.dart';
import '../../features/ledger/screens/add_customer_screen.dart';
import '../../features/ledger/screens/add_ledger_entry_screen.dart';
import '../../features/reports/screens/reports_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/orgs/screens/org_selection_screen.dart';
import 'shell_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final auth = authState.valueOrNull;
      final isLoggedIn = auth?.isLoggedIn ?? false;
      final isAuthRoute = state.matchedLocation == '/login' ||
          state.matchedLocation == '/register';
      final isOrgSelection = state.matchedLocation == '/org-selection';

      if (!isLoggedIn && !isAuthRoute) return '/login';
      if (isLoggedIn && isAuthRoute) {
        // If user has multiple orgs and hasn't picked one yet, go to org selection
        final orgs = auth?.organisations ?? [];
        if (orgs.length > 1 && auth?.currentOrgId == null) {
          return '/org-selection';
        }
        return '/dashboard';
      }
      // After login: redirect to org selection if multi-org and no selection yet
      if (isLoggedIn && !isAuthRoute && !isOrgSelection) {
        final orgs = auth?.organisations ?? [];
        if (orgs.length > 1 && auth?.currentOrgId == null) {
          return '/org-selection';
        }
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/org-selection',
        builder: (context, state) => const OrgSelectionScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => ShellScreen(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/transactions',
            builder: (context, state) => const TransactionListScreen(),
          ),
          GoRoute(
            path: '/transactions/add',
            builder: (context, state) => const AddTransactionScreen(),
          ),
          GoRoute(
            path: '/accounts',
            builder: (context, state) => const AccountListScreen(),
          ),
          GoRoute(
            path: '/accounts/add',
            builder: (context, state) => const AddAccountScreen(),
          ),
          GoRoute(
            path: '/ledger',
            builder: (context, state) => const CustomerListScreen(),
          ),
          GoRoute(
            path: '/ledger/add-customer',
            builder: (context, state) => const AddCustomerScreen(),
          ),
          GoRoute(
            path: '/ledger/customer/:id',
            builder: (context, state) {
              final customerId = state.pathParameters['id']!;
              return CustomerDetailScreen(customerId: customerId);
            },
          ),
          GoRoute(
            path: '/ledger/customer/:id/add-entry',
            builder: (context, state) {
              final customerId = state.pathParameters['id']!;
              final type =
                  state.uri.queryParameters['type'] ?? 'debit';
              return AddLedgerEntryScreen(
                customerId: customerId,
                initialType: type,
              );
            },
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (context, state) => const SettingsScreen(),
          ),
        ],
      ),
    ],
  );
});
