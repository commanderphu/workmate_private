import 'dart:convert';
import 'package:crypto/crypto.dart';

class GravatarUtils {
  /// Generates Gravatar URL from email address
  /// https://gravatar.com/avatar/HASH?s=SIZE&d=DEFAULT
  static String getGravatarUrl(String email, {int size = 200, String defaultImage = 'identicon'}) {
    // Convert email to lowercase and trim whitespace
    final normalizedEmail = email.toLowerCase().trim();

    // Generate MD5 hash
    final bytes = utf8.encode(normalizedEmail);
    final hash = md5.convert(bytes).toString();

    // Build URL
    return 'https://www.gravatar.com/avatar/$hash?s=$size&d=$defaultImage';
  }
}
