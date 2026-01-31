class Integration {
  final String id;
  final String userId;
  final String name;
  final String integrationType;
  final bool enabled;
  final Map<String, dynamic> config;
  final String syncDirection;
  final bool autoSync;
  final int syncIntervalMinutes;
  final String syncStatus;
  final DateTime? lastSyncAt;
  final String? errorLog;
  final DateTime createdAt;
  final DateTime updatedAt;

  Integration({
    required this.id,
    required this.userId,
    required this.name,
    required this.integrationType,
    this.enabled = true,
    required this.config,
    this.syncDirection = 'bidirectional',
    this.autoSync = true,
    this.syncIntervalMinutes = 15,
    this.syncStatus = 'idle',
    this.lastSyncAt,
    this.errorLog,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Integration.fromJson(Map<String, dynamic> json) {
    return Integration(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      name: json['name'] as String,
      integrationType: json['integration_type'] as String,
      enabled: json['enabled'] as bool? ?? true,
      config: json['config'] as Map<String, dynamic>,
      syncDirection: json['sync_direction'] as String? ?? 'bidirectional',
      autoSync: json['auto_sync'] as bool? ?? true,
      syncIntervalMinutes: json['sync_interval_minutes'] as int? ?? 15,
      syncStatus: json['sync_status'] as String? ?? 'idle',
      lastSyncAt: json['last_sync_at'] != null
          ? DateTime.parse(json['last_sync_at'])
          : null,
      errorLog: json['error_log'] as String?,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'name': name,
      'integration_type': integrationType,
      'enabled': enabled,
      'config': config,
      'sync_direction': syncDirection,
      'auto_sync': autoSync,
      'sync_interval_minutes': syncIntervalMinutes,
      'sync_status': syncStatus,
      'last_sync_at': lastSyncAt?.toIso8601String(),
      'error_log': errorLog,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  String get typeDisplayName {
    switch (integrationType) {
      case 'caldav':
        return 'CalDAV';
      case 'google_calendar':
        return 'Google Calendar';
      case 'outlook_calendar':
        return 'Outlook Calendar';
      default:
        return integrationType;
    }
  }

  String get syncDirectionDisplayName {
    switch (syncDirection) {
      case 'to_calendar':
        return 'Nur zu Kalender';
      case 'from_calendar':
        return 'Nur vom Kalender';
      case 'bidirectional':
        return 'Bidirektional';
      default:
        return syncDirection;
    }
  }

  bool get hasError => errorLog != null && errorLog!.isNotEmpty;

  Integration copyWith({
    String? name,
    bool? enabled,
    String? syncDirection,
    bool? autoSync,
    int? syncIntervalMinutes,
    Map<String, dynamic>? config,
  }) {
    return Integration(
      id: id,
      userId: userId,
      name: name ?? this.name,
      integrationType: integrationType,
      enabled: enabled ?? this.enabled,
      config: config ?? this.config,
      syncDirection: syncDirection ?? this.syncDirection,
      autoSync: autoSync ?? this.autoSync,
      syncIntervalMinutes: syncIntervalMinutes ?? this.syncIntervalMinutes,
      syncStatus: syncStatus,
      lastSyncAt: lastSyncAt,
      errorLog: errorLog,
      createdAt: createdAt,
      updatedAt: DateTime.now(),
    );
  }
}
