class User {
  final String id;
  final String username;
  final String email;
  final String? fullName;
  final bool isActive;
  final String timezone;
  final String language;
  final Map<String, dynamic> uiPreferences;
  final Map<String, dynamic> notificationPreferences;

  User({
    required this.id,
    required this.username,
    required this.email,
    this.fullName,
    required this.isActive,
    this.timezone = 'UTC',
    this.language = 'de',
    this.uiPreferences = const {},
    this.notificationPreferences = const {},
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as String,
      username: json['username'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      timezone: json['timezone'] as String? ?? 'UTC',
      language: json['language'] as String? ?? 'de',
      uiPreferences: (json['ui_preferences'] as Map<String, dynamic>?) ?? {},
      notificationPreferences:
          (json['notification_preferences'] as Map<String, dynamic>?) ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'full_name': fullName,
      'is_active': isActive,
      'timezone': timezone,
      'language': language,
      'ui_preferences': uiPreferences,
      'notification_preferences': notificationPreferences,
    };
  }

  String? get paperlessUrl => uiPreferences['paperless_url'] as String?;
  String? get paperlessToken => uiPreferences['paperless_token'] as String?;
  bool get pushEnabled => notificationPreferences['push_enabled'] as bool? ?? true;
  bool get emailEnabled => notificationPreferences['email_enabled'] as bool? ?? false;
  int get reminderMinutes => notificationPreferences['reminder_minutes'] as int? ?? 30;
}
