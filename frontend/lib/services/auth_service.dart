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
  Future<User> login(String username, String password, {bool stayLoggedIn = true}) async {
    final response = await _apiService.post(
      ApiConfig.authLogin,
      data: {'username': username, 'password': password},
    );

    final data = response.data;
    await _storage.write(key: 'access_token', value: data['access_token'] as String);
    if (stayLoggedIn) {
      await _storage.write(key: 'refresh_token', value: data['refresh_token'] as String);
      await _storage.write(key: 'stay_logged_in', value: 'true');
    } else {
      await _storage.delete(key: 'refresh_token');
      await _storage.delete(key: 'stay_logged_in');
    }

    final user = await getCurrentUser();
    await _storage.write(key: 'user_data', value: jsonEncode(user.toJson()));
    return user;
  }

  // Refresh access token using stored refresh token
  Future<bool> refreshToken() async {
    final refreshToken = await _storage.read(key: 'refresh_token');
    if (refreshToken == null) return false;

    try {
      final response = await _apiService.postWithHeader(
        ApiConfig.authRefresh,
        headers: {'Authorization': 'Bearer $refreshToken'},
      );
      await _storage.write(key: 'access_token', value: response.data['access_token'] as String);
      await _storage.write(key: 'refresh_token', value: response.data['refresh_token'] as String);
      return true;
    } catch (_) {
      return false;
    }
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
    } catch (_) {
    } finally {
      await _storage.delete(key: 'access_token');
      await _storage.delete(key: 'refresh_token');
      await _storage.delete(key: 'stay_logged_in');
      await _storage.delete(key: 'user_data');
    }
  }

  // Check if logged in (access token OR refresh token present)
  Future<bool> isLoggedIn() async {
    final access = await _storage.read(key: 'access_token');
    if (access != null) return true;
    final refresh = await _storage.read(key: 'refresh_token');
    return refresh != null;
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

  // Update user settings (profile + integrations + notifications)
  Future<User> updateSettings(Map<String, dynamic> data) async {
    final response = await _apiService.patch(ApiConfig.authMePatch, data: data);
    final user = User.fromJson(response.data);
    await _storage.write(key: 'user_data', value: jsonEncode(user.toJson()));
    return user;
  }
}
