# DevLens Android APK: CI Pipeline & Phone Installation Guide

This guide explains how the DevLens automated CI pipeline builds the Android APK and how to install it directly on your physical Android phone.

---

## 1. How the Automated CI Pipeline Works

Whenever code is pushed to `main` (or a release tag / manual dispatch), the GitHub Actions workflow [`.github/workflows/build-apk.yml`](../.github/workflows/build-apk.yml) triggers automatically:

1. **Test Validation:** Runs the Python backend test suite (`pytest`) and mobile test suite (`jest`).
2. **Environment Setup:** Configures Java 17 Temurin, Node.js 20, and Android SDK command-line tools.
3. **Expo Prebuild:** Generates native Android Gradle project structures via `npx expo prebuild --platform android --clean`.
4. **Gradle Compilation:** Compiles the standalone debug APK (`./gradlew assembleDebug`) containing all bundled JavaScript assets and native runtime binaries.
5. **Artifact Publishing:**
   - Uploads `devlens-v0.1.0-debug.apk` to **GitHub Actions Artifacts** (retained for 30 days).
   - Automatically attaches the `.apk` file to **GitHub Releases** for 1-tap phone download.

---

## 2. Installation Methods on Your Phone

### Option A: Direct Download via Phone Browser (Recommended & Easiest)
1. Open the browser (Chrome, Brave, Firefox) on your Android phone.
2. Navigate to your repository releases page:  
   👉 `https://github.com/Myparadox-creator/DevLense/releases`
3. Tap on the latest release and download **`devlens-v0.1.0-debug.apk`**.
4. Once downloaded, tap the file in your notification bar or Downloads folder to install.
5. If Android shows a prompt:
   - **"For your security, your phone is not allowed to install unknown apps from this source"**: Tap **Settings** -> Toggle **"Allow from this source"** -> Tap **Back** -> Tap **Install**.
   - **"Play Protect warning: Unrecognized app"**: Tap **More details** -> Tap **Install anyway** (standard for development/debug APKs).

---

### Option B: USB Cable Installation via ADB (1-Click Local Script)
If your phone is connected to your PC with a USB cable:

1. **Enable USB Debugging on your phone:**
   - Go to **Settings** -> **About Phone**.
   - Tap **Build Number** 7 times until you see *"You are now a developer!"*.
   - Go to **Settings** -> **System** -> **Developer Options**.
   - Turn on **USB Debugging**.
   - Connect your phone to your PC via USB and accept the *"Allow USB debugging from this computer"* popup.

2. **Run the Installer Script:**
   Open PowerShell in the project root and run:
   ```powershell
   .\scripts\install-to-phone.ps1
   ```
   Or specify an explicit APK path:
   ```powershell
   .\scripts\install-to-phone.ps1 -ApkPath "C:\path\to\devlens.apk"
   ```
   The script auto-detects `adb.exe`, checks device authorization, installs the APK, and immediately launches DevLens on your phone!

---

### Option C: Cloud Build via Expo EAS
If you have an Expo account and want to build in the cloud:

1. Install EAS CLI:
   ```bash
   npm install -g eas-cli
   ```
2. Log in:
   ```bash
   eas login
   ```
3. Run cloud APK build:
   ```bash
   cd mobile
   eas build -p android --profile preview
   ```
   Expo will compile the APK in the cloud and provide a QR code you can scan with your phone camera to download directly.

---

## 3. Configuring the App to Connect to Your Local Backend
Since DevLens mobile communicates with your FastAPI backend running on your PC:

1. Ensure your PC and phone are on the **same Wi-Fi network**.
2. Find your PC's local IP address:
   ```powershell
   ipconfig
   # Look for IPv4 Address, e.g., 192.168.1.15
   ```
3. Set `EXPO_PUBLIC_API_URL` before building or configure in `.env`:
   ```env
   EXPO_PUBLIC_API_URL=http://192.168.1.15:8001
   ```
4. Or if using USB cable, reverse port forward through ADB:
   ```powershell
   adb reverse tcp:8001 tcp:8001
   ```
   Then the phone can reach the backend at `http://localhost:8001`!
