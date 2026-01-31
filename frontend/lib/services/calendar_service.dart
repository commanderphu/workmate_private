import 'package:dio/dio.dart';
import '../models/calendar_event.dart';
import '../models/integration.dart';
import 'api_service.dart';
import '../config/api_config.dart';

class CalendarService {
  final ApiService _apiService = ApiService();

  // ===== Calendar Events =====

  Future<List<CalendarEvent>> getEvents({
    DateTime? startDate,
    DateTime? endDate,
    String? syncStatus,
  }) async {
    try {
      final queryParams = <String, dynamic>{};
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }
      if (syncStatus != null) {
        queryParams['sync_status'] = syncStatus;
      }

      final response = await _apiService.get(
        '${ApiConfig.Endpoints.calendar}/events/',
        queryParameters: queryParams,
      );

      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((json) => CalendarEvent.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load calendar events: $e');
    }
  }

  Future<CalendarEvent> getEvent(String eventId) async {
    try {
      final response = await _apiService.get(
        '${ApiConfig.Endpoints.calendar}/events/$eventId',
      );
      return CalendarEvent.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load calendar event: $e');
    }
  }

  Future<CalendarEvent> createEvent({
    required String title,
    required DateTime startTime,
    required DateTime endTime,
    String? description,
    bool allDay = false,
    String? location,
    String? taskId,
    String? externalCalendarId,
  }) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/events/',
        data: {
          'title': title,
          'start_time': startTime.toIso8601String(),
          'end_time': endTime.toIso8601String(),
          'description': description,
          'all_day': allDay,
          'location': location,
          'task_id': taskId,
          'external_calendar_id': externalCalendarId,
        },
      );
      return CalendarEvent.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to create calendar event: $e');
    }
  }

  Future<CalendarEvent> updateEvent(
    String eventId, {
    String? title,
    DateTime? startTime,
    DateTime? endTime,
    String? description,
    bool? allDay,
    String? location,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (title != null) data['title'] = title;
      if (startTime != null) data['start_time'] = startTime.toIso8601String();
      if (endTime != null) data['end_time'] = endTime.toIso8601String();
      if (description != null) data['description'] = description;
      if (allDay != null) data['all_day'] = allDay;
      if (location != null) data['location'] = location;

      final response = await _apiService.patch(
        '${ApiConfig.Endpoints.calendar}/events/$eventId',
        data: data,
      );
      return CalendarEvent.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to update calendar event: $e');
    }
  }

  Future<void> deleteEvent(String eventId) async {
    try {
      await _apiService.delete(
        '${ApiConfig.Endpoints.calendar}/events/$eventId',
      );
    } catch (e) {
      throw Exception('Failed to delete calendar event: $e');
    }
  }

  Future<CalendarEvent> resolveConflict(
    String eventId,
    String resolution, // 'keep_local' or 'keep_remote'
  ) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/events/$eventId/resolve-conflict',
        queryParameters: {'resolution': resolution},
      );
      return CalendarEvent.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to resolve conflict: $e');
    }
  }

  // ===== Integrations =====

  Future<List<Integration>> getIntegrations({bool? enabledOnly}) async {
    try {
      final queryParams = <String, dynamic>{};
      if (enabledOnly != null) {
        queryParams['enabled_only'] = enabledOnly;
      }

      final response = await _apiService.get(
        '${ApiConfig.Endpoints.calendar}/integrations/',
        queryParameters: queryParams,
      );

      final List<dynamic> data = response.data as List<dynamic>;
      return data.map((json) => Integration.fromJson(json)).toList();
    } catch (e) {
      throw Exception('Failed to load integrations: $e');
    }
  }

  Future<Integration> getIntegration(String integrationId) async {
    try {
      final response = await _apiService.get(
        '${ApiConfig.Endpoints.calendar}/integrations/$integrationId',
      );
      return Integration.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to load integration: $e');
    }
  }

  Future<Integration> createIntegration({
    required String name,
    required String integrationType,
    required Map<String, dynamic> config,
    Map<String, dynamic>? credentials,
    bool enabled = true,
    String syncDirection = 'bidirectional',
    bool autoSync = true,
    int syncIntervalMinutes = 15,
  }) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/integrations/',
        data: {
          'name': name,
          'integration_type': integrationType,
          'config': config,
          'credentials': credentials,
          'enabled': enabled,
          'sync_direction': syncDirection,
          'auto_sync': autoSync,
          'sync_interval_minutes': syncIntervalMinutes,
        },
      );
      return Integration.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to create integration: $e');
    }
  }

  Future<Integration> updateIntegration(
    String integrationId, {
    String? name,
    bool? enabled,
    String? syncDirection,
    bool? autoSync,
    int? syncIntervalMinutes,
    Map<String, dynamic>? config,
    Map<String, dynamic>? credentials,
  }) async {
    try {
      final data = <String, dynamic>{};
      if (name != null) data['name'] = name;
      if (enabled != null) data['enabled'] = enabled;
      if (syncDirection != null) data['sync_direction'] = syncDirection;
      if (autoSync != null) data['auto_sync'] = autoSync;
      if (syncIntervalMinutes != null) {
        data['sync_interval_minutes'] = syncIntervalMinutes;
      }
      if (config != null) data['config'] = config;
      if (credentials != null) data['credentials'] = credentials;

      final response = await _apiService.patch(
        '${ApiConfig.Endpoints.calendar}/integrations/$integrationId',
        data: data,
      );
      return Integration.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to update integration: $e');
    }
  }

  Future<void> deleteIntegration(String integrationId) async {
    try {
      await _apiService.delete(
        '${ApiConfig.Endpoints.calendar}/integrations/$integrationId',
      );
    } catch (e) {
      throw Exception('Failed to delete integration: $e');
    }
  }

  Future<Map<String, dynamic>> testIntegration(String integrationId) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/integrations/$integrationId/test',
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to test integration: $e');
    }
  }

  Future<Map<String, dynamic>> syncIntegration(
    String integrationId, {
    bool force = false,
  }) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/integrations/$integrationId/sync',
        data: {'force': force},
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to sync integration: $e');
    }
  }

  // ===== Task-Event Mapping =====

  Future<Map<String, dynamic>> syncAllTasks({bool force = false}) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/tasks/sync-all',
        queryParameters: {'force': force},
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to sync tasks: $e');
    }
  }

  Future<Map<String, dynamic>> cleanupCompletedTasks({
    int olderThanDays = 7,
  }) async {
    try {
      final response = await _apiService.post(
        '${ApiConfig.Endpoints.calendar}/tasks/cleanup-completed',
        queryParameters: {'older_than_days': olderThanDays},
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      throw Exception('Failed to cleanup completed tasks: $e');
    }
  }
}
