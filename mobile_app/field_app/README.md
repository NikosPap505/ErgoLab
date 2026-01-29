# ErgoLab Field Worker App

Mobile application για τους τεχνικούς πεδίου του ErgoLab.

## Χαρακτηριστικά

- 📱 **Barcode/QR Scanning** - Σάρωση υλικών με την κάμερα
- 📦 **Stock Management** - Εισαγωγή/Εξαγωγή υλικών στις αποθήκες
- 📷 **Photo Capture** - Λήψη και αποθήκευση φωτογραφιών
- 🔄 **Offline Mode** - Λειτουργία χωρίς σύνδεση με sync

## Εγκατάσταση

### Prerequisites

1. Flutter SDK >= 3.0.0
2. Android Studio / Xcode
3. Συσκευή Android/iOS ή Emulator

### Setup

```bash
# Navigate to project
cd mobile_app/field_app

# Get dependencies
flutter pub get

# Run on emulator/device
flutter run
```

### Build APK

```bash
# Debug APK
flutter build apk --debug

# Release APK
flutter build apk --release
```

## Configuration

Για να συνδεθεί με το backend, επεξεργαστείτε το `lib/services/api_service.dart`:

```dart
// For Android emulator
static const String baseUrl = 'http://10.0.2.2:8000';

// For physical device on same network
static const String baseUrl = 'http://YOUR_PC_IP:8000';
```

## Δομή Έργου

```
lib/
├── main.dart              # Entry point
├── providers/
│   └── app_state.dart     # App state management
├── screens/
│   ├── login_screen.dart  # Login page
│   ├── home_screen.dart   # Main dashboard
│   ├── scanner_screen.dart # Barcode scanner
│   ├── add_stock_screen.dart # Add/remove stock
│   ├── inventory_screen.dart # View inventory
│   └── capture_screen.dart # Photo capture
└── services/
    ├── api_service.dart   # Backend API calls
    ├── connectivity_service.dart # Network monitoring
    └── offline_database.dart # SQLite for offline
```

## Screens

### Login
- Email/Password authentication
- Token storage με SharedPreferences

### Home
- Επιλογή έργου και αποθήκης
- Quick actions grid

### Scanner
- Barcode/QR code scanning
- Manual SKU entry
- Auto-lookup υλικού

### Add Stock
- Εισαγωγή/Εξαγωγή υλικών
- Quick quantity buttons
- Notes support

### Inventory
- Λίστα αποθέματος
- Search functionality
- Low stock warnings

### Capture
- Camera/Gallery image selection
- Upload to backend
- Project assignment

## Offline Support

Το app αποθηκεύει τοπικά:
- Pending transactions
- Cached materials/warehouses/projects
- Pending photo uploads

Όταν επανέλθει η σύνδεση, γίνεται αυτόματος sync.
