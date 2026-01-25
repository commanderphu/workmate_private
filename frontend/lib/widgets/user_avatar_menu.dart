import 'package:flutter/material.dart';
import '../models/user.dart';
import '../utils/gravatar.dart';

class UserAvatarMenu extends StatelessWidget {
  final User user;
  final VoidCallback onProfileTap;
  final VoidCallback onSettingsTap;
  final VoidCallback onLogoutTap;

  const UserAvatarMenu({
    super.key,
    required this.user,
    required this.onProfileTap,
    required this.onSettingsTap,
    required this.onLogoutTap,
  });

  @override
  Widget build(BuildContext context) {
    final gravatarUrl = GravatarUtils.getGravatarUrl(user.email);

    return PopupMenuButton<String>(
      offset: const Offset(0, 50),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      itemBuilder: (context) => [
        // User Info Header
        PopupMenuItem<String>(
          enabled: false,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                user.fullName ?? user.username,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                user.email,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
              const Divider(height: 16),
            ],
          ),
        ),
        // Profile Option
        const PopupMenuItem<String>(
          value: 'profile',
          child: Row(
            children: [
              Icon(Icons.person_outline, size: 20),
              SizedBox(width: 12),
              Text('Profil'),
            ],
          ),
        ),
        // Settings Option
        const PopupMenuItem<String>(
          value: 'settings',
          child: Row(
            children: [
              Icon(Icons.settings_outlined, size: 20),
              SizedBox(width: 12),
              Text('Einstellungen'),
            ],
          ),
        ),
        const PopupMenuItem<String>(
          height: 1,
          enabled: false,
          child: Divider(height: 1),
        ),
        // Logout Option
        PopupMenuItem<String>(
          value: 'logout',
          child: Row(
            children: [
              Icon(Icons.logout, size: 20, color: Colors.red.shade600),
              const SizedBox(width: 12),
              Text(
                'Logout',
                style: TextStyle(color: Colors.red.shade600),
              ),
            ],
          ),
        ),
      ],
      onSelected: (value) {
        switch (value) {
          case 'profile':
            onProfileTap();
            break;
          case 'settings':
            onSettingsTap();
            break;
          case 'logout':
            onLogoutTap();
            break;
        }
      },
      child: Padding(
        padding: const EdgeInsets.all(8.0),
        child: CircleAvatar(
          radius: 18,
          backgroundColor: Colors.grey.shade300,
          backgroundImage: NetworkImage(gravatarUrl),
          onBackgroundImageError: (_, __) {
            // Fallback handled by Gravatar default image
          },
          child: Container(
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(
                color: Colors.white,
                width: 2,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
