import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiConfig {
  static String get baseUrl => dotenv.env['API_URL'] ?? 'http://localhost:8000/api/v1';

  static const int connectTimeout = 30000; // 30 seconds
  static const int receiveTimeout = 30000;

  // API Endpoints
  static const String authLogin = '/auth/login';
  static const String authRegister = '/auth/register';
  static const String authMe = '/auth/me';
  static const String authLogout = '/auth/logout';

  static const String tasks = '/tasks';
  static String taskById(String id) => '/tasks/$id';

  static const String documents = '/documents';
  static String documentById(String id) => '/documents/$id';
}
