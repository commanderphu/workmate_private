import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/api_config.dart';
import '../models/user.dart';
import 'api_service.dart';

class AuthService {
  final ApiService _apiService = ApiService();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  // Login
  Future<User> login(String username, String password) async {
    final response = await _apiService.post(
      ApiConfig.authLogin,
      data: {
        'username': username,
        'password': password,
      },
    );

    final data = response.data;
    final token = data['access_token'] as String;

    // Store token
    await _storage.write(key: 'access_token', value: token);

    // Get user data
    final user = await getCurrentUser();

    // Store user data
    await _storage.write(key: 'user_data', value: jsonEncode(user.toJson()));

    return user;
  }

  // Register
  Future<User> register({
    required String username,
    required String email,
    required String password,
  }) async {
    final response = await _apiService.post(
      ApiConfig.authRegister,
      data: {
        'username': username,
        'email': email,
        'password': password,
      },
    );

    return User.fromJson(response.data);
  }

  // Get current user
  Future<User> getCurrentUser() async {
    final response = await _apiService.get(ApiConfig.authMe);
    return User.fromJson(response.data);
  }

  // Logout
  Future<void> logout() async {
    try {
      await _apiService.post(ApiConfig.authLogout);
    } catch (e) {
      // Ignore errors on logout
    } finally {
      await _storage.delete(key: 'access_token');
      await _storage.delete(key: 'user_data');
    }
  }

  // Check if logged in
  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'access_token');
    return token != null;
  }

  // Get stored user
  Future<User?> getStoredUser() async {
    final userDataString = await _storage.read(key: 'user_data');
    if (userDataString == null) return null;

    try {
      final userData = jsonDecode(userDataString);
      return User.fromJson(userData);
    } catch (e) {
      return null;
    }
  }

  // Get stored token
  Future<String?> getToken() async {
    return await _storage.read(key: 'access_token');
  }
}
