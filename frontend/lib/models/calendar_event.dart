class CalendarEvent {
  final String id;
  final String userId;
  final String? taskId;
  final String title;
  final String? description;
  final DateTime startTime;
  final DateTime endTime;
  final bool allDay;
  final String? location;
  final String? externalEventId;
  final String? externalCalendarId;
  final String syncStatus;
  final DateTime? lastSyncedAt;
  final Map<String, dynamic>? conflictData;
  final DateTime createdAt;
  final DateTime updatedAt;

  CalendarEvent({
    required this.id,
    required this.userId,
    this.taskId,
    required this.title,
    this.description,
    required this.startTime,
    required this.endTime,
    this.allDay = false,
    this.location,
    this.externalEventId,
    this.externalCalendarId,
    required this.syncStatus,
    this.lastSyncedAt,
    this.conflictData,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CalendarEvent.fromJson(Map<String, dynamic> json) {
    return CalendarEvent(
      id: json['id'] as String,
      userId: json['user_id'] as String,
      taskId: json['task_id'] as String?,
      title: json['title'] as String,
      description: json['description'] as String?,
      startTime: DateTime.parse(json['start_time']),
      endTime: DateTime.parse(json['end_time']),
      allDay: json['all_day'] as bool? ?? false,
      location: json['location'] as String?,
      externalEventId: json['external_event_id'] as String?,
      externalCalendarId: json['external_calendar_id'] as String?,
      syncStatus: json['sync_status'] as String? ?? 'pending',
      lastSyncedAt: json['last_synced_at'] != null
          ? DateTime.parse(json['last_synced_at'])
          : null,
      conflictData: json['conflict_data'] as Map<String, dynamic>?,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'user_id': userId,
      'task_id': taskId,
      'title': title,
      'description': description,
      'start_time': startTime.toIso8601String(),
      'end_time': endTime.toIso8601String(),
      'all_day': allDay,
      'location': location,
      'external_event_id': externalEventId,
      'external_calendar_id': externalCalendarId,
      'sync_status': syncStatus,
      'last_synced_at': lastSyncedAt?.toIso8601String(),
      'conflict_data': conflictData,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  bool get hasConflict => syncStatus == 'conflict';
  bool get isSynced => syncStatus == 'synced';
  bool get isPending => syncStatus == 'pending';
  bool get hasFailed => syncStatus == 'failed';

  bool get isToday {
    final now = DateTime.now();
    final eventDate = startTime;
    return eventDate.year == now.year &&
        eventDate.month == now.month &&
        eventDate.day == now.day;
  }

  bool get isUpcoming {
    return startTime.isAfter(DateTime.now());
  }

  bool get isPast {
    return endTime.isBefore(DateTime.now());
  }

  Duration get duration {
    return endTime.difference(startTime);
  }

  CalendarEvent copyWith({
    String? title,
    String? description,
    DateTime? startTime,
    DateTime? endTime,
    bool? allDay,
    String? location,
    String? syncStatus,
  }) {
    return CalendarEvent(
      id: id,
      userId: userId,
      taskId: taskId,
      title: title ?? this.title,
      description: description ?? this.description,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      allDay: allDay ?? this.allDay,
      location: location ?? this.location,
      externalEventId: externalEventId,
      externalCalendarId: externalCalendarId,
      syncStatus: syncStatus ?? this.syncStatus,
      lastSyncedAt: lastSyncedAt,
      conflictData: conflictData,
      createdAt: createdAt,
      updatedAt: DateTime.now(),
    );
  }
}
