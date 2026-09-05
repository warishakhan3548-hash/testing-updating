import java.io.File
import java.net.URL
import java.util.zip.ZipFile

plugins {
    id("com.android.application")
    id("dev.flutter.flutter-gradle-plugin")
}

val offlineVoiceModel =
    rootProject.projectDir.parentFile.resolve("assets/models/vosk-model-small-hi-0.22.zip")
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
    description = "Ensures the bundled offline Hindi Vosk model exists before Flutter assets are compiled."
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

        logger.lifecycle("Downloading offline Hindi voice model for APK bundling…")
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
                "Could not prepare the offline Hindi voice model required by pubspec.yaml.",
                error,
            )
        }
    }
}

tasks.configureEach {
    if (name.startsWith("compileFlutterBuild")) {
        dependsOn(prepareOfflineVoiceModel)
    }
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
