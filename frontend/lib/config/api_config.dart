import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  static const _prefKey = 'custom_api_url';
  static String? _runtimeUrl;

  static Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _runtimeUrl = prefs.getString(_prefKey);
  }

  static Future<void> setBaseUrl(String url) async {
    _runtimeUrl = url.isEmpty ? null : url;
    final prefs = await SharedPreferences.getInstance();
    if (url.isEmpty) {
      await prefs.remove(_prefKey);
    } else {
      await prefs.setString(_prefKey, url);
    }
  }

  static String get baseUrl =>
      _runtimeUrl ?? dotenv.env['API_URL'] ?? 'http://localhost:8000/api/v1';

  static const int connectTimeout = 30000; // 30 seconds
  static const int receiveTimeout = 30000;

  // API Endpoints (with trailing slashes for FastAPI)
  static const String authLogin = '/auth/login';
  static const String authRegister = '/auth/register';
  static const String authMe = '/auth/me';
  static const String authLogout = '/auth/logout';
  static const String authMePatch = '/auth/me';

  static const String tasks = '/tasks/';
  static String taskById(String id) => '/tasks/$id';

  static const String documents = '/documents/';
  static String documentById(String id) => '/documents/$id';

  static const String calendar = '/calendar';
}
