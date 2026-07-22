import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

// Workmate Design Tokens v1.0.0
class WmColors {
  static const primary           = Color(0xFFF59E0B);
  static const primaryLight      = Color(0xFFFDBA1F);
  static const success           = Color(0xFF10B981);
  static const error             = Color(0xFFEF4444);
  static const warning           = Color(0xFFFBBF24);
  static const info              = Color(0xFF3B82F6);

  static const backgroundDark    = Color(0xFF1E1E1E);
  static const surfaceDark       = Color(0xFF2D2D2D);
  static const borderDark        = Color(0xFF3A3A3A);
  static const textPrimaryDark   = Color(0xFFF5F7FA);
  static const textSecondaryDark = Color(0xFFA7ADB7);

  static const backgroundLight    = Color(0xFFF7F8FA);
  static const surfaceLight       = Color(0xFFFFFFFF);
  static const borderLight        = Color(0xFFD7DBE0);
  static const textPrimaryLight   = Color(0xFF1E1E1E);
  static const textSecondaryLight = Color(0xFF6B7280);
}

class ThemeProvider extends ChangeNotifier {
  bool _isDarkMode = true;

  bool get isDarkMode => _isDarkMode;
  Color get accentColor => WmColors.primary;

  ThemeProvider() {
    _loadPreferences();
  }

  ThemeData get theme => _isDarkMode ? _darkTheme : _lightTheme;

  static ThemeData get _darkTheme {
    final base = GoogleFonts.interTextTheme(ThemeData.dark().textTheme);
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: WmColors.backgroundDark,
      colorScheme: const ColorScheme.dark(
        primary:    WmColors.primary,
        onPrimary:  Color(0xFF111827),
        secondary:  WmColors.success,
        onSecondary: Color(0xFF111827),
        error:      WmColors.error,
        surface:    WmColors.surfaceDark,
        onSurface:  WmColors.textPrimaryDark,
        outline:    WmColors.borderDark,
      ),
      textTheme: base.copyWith(
        displayLarge:   base.displayLarge?.copyWith(color: WmColors.textPrimaryDark, fontWeight: FontWeight.w700),
        headlineLarge:  base.headlineLarge?.copyWith(color: WmColors.textPrimaryDark, fontWeight: FontWeight.w700),
        headlineMedium: base.headlineMedium?.copyWith(color: WmColors.textPrimaryDark, fontWeight: FontWeight.w600),
        bodyLarge:      base.bodyLarge?.copyWith(color: WmColors.textPrimaryDark),
        bodyMedium:     base.bodyMedium?.copyWith(color: WmColors.textPrimaryDark),
        bodySmall:      base.bodySmall?.copyWith(color: WmColors.textSecondaryDark),
        labelSmall:     base.labelSmall?.copyWith(color: WmColors.textSecondaryDark, fontWeight: FontWeight.w600),
      ),
      cardTheme: CardThemeData(
        color: WmColors.surfaceDark,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: WmColors.borderDark),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: WmColors.primary,
          foregroundColor: const Color(0xFF111827),
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: WmColors.textPrimaryDark,
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          side: const BorderSide(color: WmColors.borderDark),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: WmColors.surfaceDark,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.borderDark)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.borderDark)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.primary, width: 2)),
        labelStyle: const TextStyle(color: WmColors.textSecondaryDark),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: WmColors.surfaceDark,
        foregroundColor: WmColors.textPrimaryDark,
        elevation: 0,
        titleTextStyle: GoogleFonts.inter(color: WmColors.textPrimaryDark, fontSize: 18, fontWeight: FontWeight.w600),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: WmColors.surfaceDark,
        indicatorColor: WmColors.primary.withOpacity(0.2),
        iconTheme: WidgetStateProperty.resolveWith((s) => IconThemeData(
          color: s.contains(WidgetState.selected) ? WmColors.primary : WmColors.textSecondaryDark,
        )),
        labelTextStyle: WidgetStateProperty.resolveWith((s) => GoogleFonts.inter(
          color: s.contains(WidgetState.selected) ? WmColors.primary : WmColors.textSecondaryDark,
          fontWeight: s.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w400,
          fontSize: 12,
        )),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: WmColors.borderDark,
        labelStyle: const TextStyle(color: WmColors.textPrimaryDark),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
      dividerTheme: const DividerThemeData(color: WmColors.borderDark),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: WmColors.primary,
        foregroundColor: Color(0xFF111827),
      ),
    );
  }

  static ThemeData get _lightTheme {
    final base = GoogleFonts.interTextTheme(ThemeData.light().textTheme);
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: WmColors.backgroundLight,
      colorScheme: const ColorScheme.light(
        primary:    WmColors.primary,
        onPrimary:  Color(0xFF111827),
        secondary:  WmColors.success,
        onSecondary: Color(0xFF111827),
        error:      WmColors.error,
        surface:    WmColors.surfaceLight,
        onSurface:  WmColors.textPrimaryLight,
        outline:    WmColors.borderLight,
      ),
      textTheme: base.copyWith(
        displayLarge:   base.displayLarge?.copyWith(color: WmColors.textPrimaryLight, fontWeight: FontWeight.w700),
        headlineLarge:  base.headlineLarge?.copyWith(color: WmColors.textPrimaryLight, fontWeight: FontWeight.w700),
        headlineMedium: base.headlineMedium?.copyWith(color: WmColors.textPrimaryLight, fontWeight: FontWeight.w600),
        bodyLarge:      base.bodyLarge?.copyWith(color: WmColors.textPrimaryLight),
        bodyMedium:     base.bodyMedium?.copyWith(color: WmColors.textPrimaryLight),
        bodySmall:      base.bodySmall?.copyWith(color: WmColors.textSecondaryLight),
        labelSmall:     base.labelSmall?.copyWith(color: WmColors.textSecondaryLight, fontWeight: FontWeight.w600),
      ),
      cardTheme: CardThemeData(
        color: WmColors.surfaceLight,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: WmColors.borderLight),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: WmColors.primary,
          foregroundColor: const Color(0xFF111827),
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.inter(fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: WmColors.textPrimaryLight,
          minimumSize: const Size(0, 44),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          side: const BorderSide(color: WmColors.borderLight),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: WmColors.surfaceLight,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.borderLight)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.borderLight)),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: WmColors.primary, width: 2)),
        labelStyle: const TextStyle(color: WmColors.textSecondaryLight),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: WmColors.surfaceLight,
        foregroundColor: WmColors.textPrimaryLight,
        elevation: 0,
        titleTextStyle: GoogleFonts.inter(color: WmColors.textPrimaryLight, fontSize: 18, fontWeight: FontWeight.w600),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: WmColors.surfaceLight,
        indicatorColor: WmColors.primary.withOpacity(0.15),
        iconTheme: WidgetStateProperty.resolveWith((s) => IconThemeData(
          color: s.contains(WidgetState.selected) ? WmColors.primary : WmColors.textSecondaryLight,
        )),
        labelTextStyle: WidgetStateProperty.resolveWith((s) => GoogleFonts.inter(
          color: s.contains(WidgetState.selected) ? WmColors.primary : WmColors.textSecondaryLight,
          fontWeight: s.contains(WidgetState.selected) ? FontWeight.w600 : FontWeight.w400,
          fontSize: 12,
        )),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: WmColors.borderLight,
        labelStyle: const TextStyle(color: WmColors.textPrimaryLight),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
      dividerTheme: const DividerThemeData(color: WmColors.borderLight),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: WmColors.primary,
        foregroundColor: Color(0xFF111827),
      ),
    );
  }

  void toggleDarkMode() {
    _isDarkMode = !_isDarkMode;
    _savePreferences();
    notifyListeners();
  }

  void setAccentColor(Color color) {} // Kein Custom Accent mehr — Design-Tokens sind fix

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    _isDarkMode = prefs.getBool('isDarkMode') ?? true;
    notifyListeners();
  }

  Future<void> _savePreferences() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isDarkMode', _isDarkMode);
  }
}
