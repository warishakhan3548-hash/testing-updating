import java.io.File
import java.net.URL
import java.util.zip.ZipFile

plugins {
    id("com.android.application")
    // The project currently uses Flutter/AGP 9's legacy Kotlin mode
    // (android.builtInKotlin=false). KGP must therefore be applied explicitly
    // so MainActivity.kt and the native voice MethodChannel are compiled.
    id("org.jetbrains.kotlin.android")
    id("dev.flutter.flutter-gradle-plugin")
}

val offlineVoiceModel =
    projectDir.resolve("src/main/assets/vosk-model-small-hi-0.22.zip")
val offlineVoiceModelUrl =
    "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"

fun isUsableOfflineVoiceModel(file: File): Boolean {
    if (!file.isFile || file.length() < 10_000_000L) return false
    return try {
        ZipFile(file).use { zip ->
            val entries = zip.entries()
            var hasAcousticModel = false
            while (entries.hasMoreElements()) {
                val name = entries.nextElement().name
                if (name.endsWith("/am/final.mdl") || name == "am/final.mdl") {
                    hasAcousticModel = true
                    break
                }
            }
            hasAcousticModel
        }
    } catch (_: Exception) {
        false
    }
}

val prepareOfflineVoiceModel by tasks.registering {
    group = "voice ludo"
    description = "Ensures the native Android Vosk model asset exists before Android assets are merged."
    outputs.file(offlineVoiceModel)

    doLast {
        if (isUsableOfflineVoiceModel(offlineVoiceModel)) {
            logger.lifecycle(
                "Offline Hindi voice model ready (${offlineVoiceModel.length() / (1024 * 1024)} MB).",
            )
            return@doLast
        }

        offlineVoiceModel.parentFile.mkdirs()
        val partial = File(offlineVoiceModel.absolutePath + ".part")
        partial.delete()

        logger.lifecycle("Downloading offline Hindi Vosk model for native APK assets…")
        try {
            val connection = URL(offlineVoiceModelUrl).openConnection().apply {
                connectTimeout = 30_000
                readTimeout = 180_000
                setRequestProperty("User-Agent", "VoiceLudoMasti-Android-Build")
            }
            connection.getInputStream().use { input ->
                partial.outputStream().buffered().use { output ->
                    input.copyTo(output)
                }
            }

            if (!isUsableOfflineVoiceModel(partial)) {
                throw GradleException("Downloaded offline Hindi voice model is missing, too small, or corrupt.")
            }

            if (offlineVoiceModel.exists() && !offlineVoiceModel.delete()) {
                throw GradleException("Could not replace the previous offline voice model asset.")
            }
            if (!partial.renameTo(offlineVoiceModel)) {
                partial.copyTo(offlineVoiceModel, overwrite = true)
                partial.delete()
            }

            if (!isUsableOfflineVoiceModel(offlineVoiceModel)) {
                throw GradleException("Offline Hindi voice model failed final integrity verification.")
            }
            logger.lifecycle(
                "Offline Hindi voice model prepared (${offlineVoiceModel.length() / (1024 * 1024)} MB).",
            )
        } catch (error: Exception) {
            partial.delete()
            throw GradleException(
                "Could not prepare the native Android offline Hindi voice model asset.",
                error,
            )
        }
    }
}

// The model is a native Android asset, not a Flutter asset. Preparing it at
// preBuild guarantees it exists before Android's mergeAssets/package steps,
// while Flutter asset bundling no longer depends on a generated ZIP file.
tasks.named("preBuild") {
    dependsOn(prepareOfflineVoiceModel)
}

android {
    namespace = "com.aaris.voiceludomasti"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "com.aaris.voiceludomasti"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
