import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("dev.flutter.flutter-gradle-plugin")
    id("com.google.gms.google-services")
}

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    FileInputStream(keystorePropertiesFile).use { keystoreProperties.load(it) }
}

val cmKeystorePath = System.getenv("CM_KEYSTORE_PATH")
val cmKeystorePassword = System.getenv("CM_KEYSTORE_PASSWORD")
val cmKeyAlias = System.getenv("CM_KEY_ALIAS")
val cmKeyPassword = System.getenv("CM_KEY_PASSWORD")
val hasCodemagicSigning = listOf(
    cmKeystorePath,
    cmKeystorePassword,
    cmKeyAlias,
    cmKeyPassword,
).all { !it.isNullOrBlank() }
val hasLocalSigning = keystorePropertiesFile.exists() &&
    listOf("storeFile", "storePassword", "keyAlias", "keyPassword").all {
        !keystoreProperties.getProperty(it).isNullOrBlank()
    }
val hasReleaseSigning = hasCodemagicSigning || hasLocalSigning

android {
    namespace = "com.aaris.diary.financial"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.aaris.diary.financial"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        multiDexEnabled = true
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                if (hasCodemagicSigning) {
                    storeFile = file(cmKeystorePath!!)
                    storePassword = cmKeystorePassword!!
                    keyAlias = cmKeyAlias!!
                    keyPassword = cmKeyPassword!!
                } else {
                    storeFile = file(keystoreProperties.getProperty("storeFile"))
                    storePassword = keystoreProperties.getProperty("storePassword")
                    keyAlias = keystoreProperties.getProperty("keyAlias")
                    keyPassword = keystoreProperties.getProperty("keyPassword")
                }
            }
        }
    }

    buildTypes {
        release {
            // Codemagic supplies CM_* values; local builds use android/key.properties.
            // The debug fallback keeps unsigned developer checkouts buildable.
            signingConfig = if (hasReleaseSigning) {
                signingConfigs.getByName("release")
            } else {
                signingConfigs.getByName("debug")
            }
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
}

flutter {
    source = "../.."
}
