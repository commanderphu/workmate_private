import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../config/api_config.dart';

class ApiService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  void updateBaseUrl(String url) {
    _dio.options.baseUrl = url;
  }

  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(milliseconds: ApiConfig.connectTimeout),
        receiveTimeout: const Duration(milliseconds: ApiConfig.receiveTimeout),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _setupInterceptors();
  }

  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'access_token');
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          return handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401 &&
              error.requestOptions.extra['_retry'] != true) {
            final refreshToken = await _storage.read(key: 'refresh_token');
            if (refreshToken != null) {
              try {
                final refreshResponse = await _dio.post(
                  ApiConfig.authRefresh,
                  options: Options(
                    headers: {'Authorization': 'Bearer $refreshToken'},
                    extra: {'_retry': true},
                  ),
                );
                final newAccess = refreshResponse.data['access_token'] as String;
                final newRefresh = refreshResponse.data['refresh_token'] as String;
                await _storage.write(key: 'access_token', value: newAccess);
                await _storage.write(key: 'refresh_token', value: newRefresh);

                // Retry original request with new token
                final retryOptions = error.requestOptions;
                retryOptions.headers['Authorization'] = 'Bearer $newAccess';
                retryOptions.extra['_retry'] = true;
                final retryResponse = await _dio.fetch(retryOptions);
                return handler.resolve(retryResponse);
              } catch (_) {
                // Refresh failed — clear all and let the 401 propagate
                await _storage.delete(key: 'access_token');
                await _storage.delete(key: 'refresh_token');
                await _storage.delete(key: 'stay_logged_in');
                await _storage.delete(key: 'user_data');
              }
            } else {
              await _storage.delete(key: 'access_token');
              await _storage.delete(key: 'user_data');
            }
          }
          return handler.next(error);
        },
      ),
    );
  }

  Dio get dio => _dio;

  // Helper methods
  Future<Response> get(String path, {Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.get(path, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> post(String path, {dynamic data, Map<String, dynamic>? queryParameters}) async {
    try {
      return await _dio.post(path, data: data, queryParameters: queryParameters);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> postWithHeader(String path,
      {dynamic data, required Map<String, String> headers}) async {
    try {
      return await _dio.post(path,
          data: data, options: Options(headers: headers, extra: {'_retry': true}));
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> patch(String path, {dynamic data}) async {
    try {
      return await _dio.patch(path, data: data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Future<Response> delete(String path) async {
    try {
      return await _dio.delete(path);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timeout. Please check your internet connection.';
      case DioExceptionType.badResponse:
        return _extractErrorMessage(error.response);
      case DioExceptionType.cancel:
        return 'Request cancelled';
      default:
        return 'Network error. Please try again.';
    }
  }

  String _extractErrorMessage(Response? response) {
    if (response?.data != null) {
      if (response!.data is Map) {
        return response.data['detail'] ?? response.data['message'] ?? 'Server error';
      }
      return response.data.toString();
    }
    return 'Server error (${response?.statusCode})';
  }
}
