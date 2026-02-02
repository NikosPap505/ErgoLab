import 'package:flutter_test/flutter_test.dart';
import 'package:field_app/l10n/app_localizations.dart';
import 'package:flutter/material.dart';

void main() {
  group('AppLocalizations', () {
    test('supports Greek locale', () {
      const greekLocale = Locale('el');
      final l10n = AppLocalizations(greekLocale);

      expect(l10n.locale.languageCode, equals('el'));
    });

    test('supports English locale', () {
      const englishLocale = Locale('en');
      final l10n = AppLocalizations(englishLocale);

      expect(l10n.locale.languageCode, equals('en'));
    });

    test('returns Greek translations for el locale', () {
      const greekLocale = Locale('el');
      final l10n = AppLocalizations(greekLocale);

      expect(l10n.notificationSettings, equals('Ρυθμίσεις Ειδοποιήσεων'));
      expect(l10n.scanHistory, equals('Ιστορικό Σαρώσεων'));
    });

    test('returns English translations for en locale', () {
      const englishLocale = Locale('en');
      final l10n = AppLocalizations(englishLocale);

      expect(l10n.notificationSettings, equals('Notification Settings'));
      expect(l10n.scanHistory, equals('Scan History'));
    });

    test('falls back to Greek for unsupported locale', () {
      const frenchLocale = Locale('fr');
      final l10n = AppLocalizations(frenchLocale);

      // Should fall back to Greek (default)
      expect(l10n.notificationSettings, equals('Ρυθμίσεις Ειδοποιήσεων'));
    });

    test('supportedLocales contains el and en', () {
      expect(
        AppLocalizations.supportedLocales,
        containsAll([const Locale('el'), const Locale('en')]),
      );
    });

    test('delegate isSupported returns true for el', () {
      expect(
        AppLocalizations.delegate.isSupported(const Locale('el')),
        isTrue,
      );
    });

    test('delegate isSupported returns true for en', () {
      expect(
        AppLocalizations.delegate.isSupported(const Locale('en')),
        isTrue,
      );
    });

    test('delegate isSupported returns false for unsupported locale', () {
      expect(
        AppLocalizations.delegate.isSupported(const Locale('fr')),
        isFalse,
      );
    });
  });
}
