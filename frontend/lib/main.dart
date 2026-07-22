import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:provider/provider.dart';
import 'firebase_options.dart';
import 'providers/auth_provider.dart';
import 'providers/document_provider.dart';
import 'providers/task_provider.dart';
import 'providers/theme_provider.dart';
import 'config/api_config.dart';
import 'pages/dashboard_page.dart';
import 'pages/login_page.dart';
import 'services/push_notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('de_DE', null);

  // Load environment variables
  await dotenv.load(fileName: '.env');
  await ApiConfig.init();

  // Initialize Firebase (requires google-services.json / GoogleService-Info.plist)
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => TaskProvider()),
        ChangeNotifierProvider(create: (_) => DocumentProvider()),
      ],
      child: const WorkmateApp(),
    ),
  );
}

class WorkmateApp extends StatelessWidget {
  const WorkmateApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ThemeProvider>(
      builder: (context, themeProvider, child) {
        return MaterialApp(
          title: 'Workmate Private',
          theme: themeProvider.theme,
          home: const AuthWrapper(),
          debugShowCheckedModeBanner: false,
        );
      },
    );
  }
}

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  final _pushService = PushNotificationService();
  bool _pushInitialized = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AuthProvider>().initialize();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, authProvider, child) {
        if (authProvider.status == AuthStatus.initial ||
            authProvider.status == AuthStatus.loading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (authProvider.status == AuthStatus.unauthenticated) {
          _pushInitialized = false;
          return const LoginPage();
        }

        // Initialize push notifications once after login
        if (!_pushInitialized) {
          _pushInitialized = true;
          _pushService.initialize();
        }

        return const DashboardPage();
      },
    );
  }
}
