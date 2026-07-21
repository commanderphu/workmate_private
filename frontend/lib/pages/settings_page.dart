import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flex_color_picker/flex_color_picker.dart';
import '../providers/auth_provider.dart';
import '../providers/theme_provider.dart';
import '../services/auth_service.dart';
import '../models/user.dart';
import '../utils/gravatar.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final AuthService _authService = AuthService();
  bool _saving = false;

  // Profil
  late TextEditingController _fullNameCtrl;

  // Paperless
  late TextEditingController _paperlessUrlCtrl;
  late TextEditingController _paperlessTokenCtrl;
  bool _paperlessTokenVisible = false;

  // Benachrichtigungen
  bool _pushEnabled = true;
  bool _emailEnabled = false;
  int _reminderMinutes = 30;

  // Einstellungen
  String _timezone = 'Europe/Berlin';
  String _language = 'de';

  User? _user;

  @override
  void initState() {
    super.initState();
    _fullNameCtrl = TextEditingController();
    _paperlessUrlCtrl = TextEditingController();
    _paperlessTokenCtrl = TextEditingController();
    _loadUser();
  }

  @override
  void dispose() {
    _fullNameCtrl.dispose();
    _paperlessUrlCtrl.dispose();
    _paperlessTokenCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadUser() async {
    final user = await _authService.getCurrentUser();
    setState(() {
      _user = user;
      _fullNameCtrl.text = user.fullName ?? '';
      _paperlessUrlCtrl.text = user.paperlessUrl ?? '';
      _paperlessTokenCtrl.text = user.paperlessToken ?? '';
      _pushEnabled = user.pushEnabled;
      _emailEnabled = user.emailEnabled;
      _reminderMinutes = user.reminderMinutes;
      _timezone = user.timezone;
      _language = user.language;
    });
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final payload = <String, dynamic>{
        'full_name': _fullNameCtrl.text.trim(),
        'timezone': _timezone,
        'language': _language,
        'notifications_push_enabled': _pushEnabled,
        'notifications_email_enabled': _emailEnabled,
        'notifications_reminder_minutes': _reminderMinutes,
      };

      final paperlessUrl = _paperlessUrlCtrl.text.trim();
      final paperlessToken = _paperlessTokenCtrl.text.trim();
      if (paperlessUrl.isNotEmpty) payload['paperless_url'] = paperlessUrl;
      if (paperlessToken.isNotEmpty) payload['paperless_token'] = paperlessToken;

      final updated = await _authService.updateSettings(payload);

      if (mounted) {
        final auth = context.read<AuthProvider>();
        auth.setUser(updated);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Einstellungen gespeichert')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Einstellungen'),
        actions: [
          if (_saving)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            TextButton.icon(
              onPressed: _save,
              icon: const Icon(Icons.save),
              label: const Text('Speichern'),
            ),
        ],
      ),
      body: _user == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: [
                _sectionHeader(context, 'Profil', Icons.person),
                _buildProfil(theme),
                _sectionHeader(context, 'Paperless NGX', Icons.folder_copy),
                _buildPaperless(theme),
                _sectionHeader(context, 'Benachrichtigungen', Icons.notifications),
                _buildNotifications(theme),
                _sectionHeader(context, 'Darstellung', Icons.palette),
                _buildAppearance(context, themeProvider),
                const SizedBox(height: 24),
              ],
            ),
    );
  }

  Widget _sectionHeader(BuildContext context, String title, IconData icon) {
    final themeProvider = Provider.of<ThemeProvider>(context, listen: false);
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: themeProvider.accentColor),
          const SizedBox(width: 8),
          Text(
            title,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: themeProvider.accentColor,
                  letterSpacing: 0.5,
                ),
          ),
        ],
      ),
    );
  }

  Widget _buildProfil(ThemeData theme) {
    final themeProvider = Provider.of<ThemeProvider>(context, listen: false);
    final accent = themeProvider.accentColor;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Column(
        children: [
          // Avatar-Header
          if (_user != null)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [accent.withValues(alpha: 0.15), accent.withValues(alpha: 0.03)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              ),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundImage: NetworkImage(
                      GravatarUtils.getGravatarUrl(_user!.email, size: 150),
                    ),
                    backgroundColor: accent.withValues(alpha: 0.2),
                    child: null,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _user!.fullName ?? _user!.username,
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _user!.email,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                    decoration: BoxDecoration(
                      color: accent.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      '@${_user!.username}',
                      style: theme.textTheme.labelSmall?.copyWith(color: accent),
                    ),
                  ),
                ],
              ),
            ),
          // Formfelder
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
            TextField(
              controller: _fullNameCtrl,
              decoration: const InputDecoration(
                labelText: 'Anzeigename',
                prefixIcon: Icon(Icons.badge),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _language,
              decoration: const InputDecoration(
                labelText: 'Sprache',
                prefixIcon: Icon(Icons.language),
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'de', child: Text('Deutsch')),
                DropdownMenuItem(value: 'en', child: Text('English')),
              ],
              onChanged: (v) => setState(() => _language = v!),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _timezone,
              decoration: const InputDecoration(
                labelText: 'Zeitzone',
                prefixIcon: Icon(Icons.schedule),
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'Europe/Berlin', child: Text('Europe/Berlin')),
                DropdownMenuItem(value: 'UTC', child: Text('UTC')),
                DropdownMenuItem(value: 'Europe/London', child: Text('Europe/London')),
                DropdownMenuItem(value: 'America/New_York', child: Text('America/New_York')),
              ],
              onChanged: (v) => setState(() => _timezone = v!),
            ),
          ],
        ),
          ),
        ],
      ),
    );
  }

  Widget _buildPaperless(ThemeData theme) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _paperlessUrlCtrl,
              keyboardType: TextInputType.url,
              decoration: const InputDecoration(
                labelText: 'Paperless URL',
                hintText: 'https://paperless.example.com',
                prefixIcon: Icon(Icons.link),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _paperlessTokenCtrl,
              obscureText: !_paperlessTokenVisible,
              decoration: InputDecoration(
                labelText: 'API Token',
                prefixIcon: const Icon(Icons.key),
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  icon: Icon(
                    _paperlessTokenVisible ? Icons.visibility_off : Icons.visibility,
                  ),
                  onPressed: () =>
                      setState(() => _paperlessTokenVisible = !_paperlessTokenVisible),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNotifications(ThemeData theme) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Column(
        children: [
          SwitchListTile(
            title: const Text('Push-Benachrichtigungen'),
            subtitle: const Text('Erinnerungen auf dem Gerät'),
            secondary: const Icon(Icons.phone_android),
            value: _pushEnabled,
            onChanged: (v) => setState(() => _pushEnabled = v),
          ),
          const Divider(height: 1),
          SwitchListTile(
            title: const Text('E-Mail-Benachrichtigungen'),
            secondary: const Icon(Icons.email),
            value: _emailEnabled,
            onChanged: (v) => setState(() => _emailEnabled = v),
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.timer),
            title: const Text('Erinnerung vor Fälligkeit'),
            trailing: DropdownButton<int>(
              value: _reminderMinutes,
              underline: const SizedBox(),
              items: const [
                DropdownMenuItem(value: 10, child: Text('10 Min')),
                DropdownMenuItem(value: 15, child: Text('15 Min')),
                DropdownMenuItem(value: 30, child: Text('30 Min')),
                DropdownMenuItem(value: 60, child: Text('1 Std')),
                DropdownMenuItem(value: 1440, child: Text('1 Tag')),
              ],
              onChanged: (v) => setState(() => _reminderMinutes = v!),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppearance(BuildContext context, ThemeProvider themeProvider) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Column(
        children: [
          SwitchListTile(
            title: const Text('Dark Mode'),
            secondary: Icon(
              themeProvider.isDarkMode ? Icons.dark_mode : Icons.light_mode,
            ),
            value: themeProvider.isDarkMode,
            onChanged: (_) => themeProvider.toggleDarkMode(),
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.palette),
            title: const Text('Akzentfarbe'),
            trailing: GestureDetector(
              onTap: () => _showColorPicker(context, themeProvider),
              child: Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: themeProvider.accentColor,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: themeProvider.accentColor.withValues(alpha: 0.4),
                      blurRadius: 6,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showColorPicker(BuildContext context, ThemeProvider themeProvider) {
    showDialog(
      context: context,
      builder: (context) {
        Color tempColor = themeProvider.accentColor;
        return AlertDialog(
          title: const Text('Akzentfarbe wählen'),
          content: SingleChildScrollView(
            child: ColorPicker(
              color: tempColor,
              onColorChanged: (color) => tempColor = color,
              width: 40,
              height: 40,
              borderRadius: 8,
              spacing: 5,
              runSpacing: 5,
              wheelDiameter: 155,
              showMaterialName: true,
              showColorName: true,
              showColorCode: true,
              pickersEnabled: const {
                ColorPickerType.both: false,
                ColorPickerType.primary: true,
                ColorPickerType.accent: true,
                ColorPickerType.bw: false,
                ColorPickerType.custom: false,
                ColorPickerType.wheel: true,
              },
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Abbrechen'),
            ),
            ElevatedButton(
              onPressed: () {
                themeProvider.setAccentColor(tempColor);
                Navigator.of(context).pop();
              },
              child: const Text('Übernehmen'),
            ),
          ],
        );
      },
    );
  }
}
