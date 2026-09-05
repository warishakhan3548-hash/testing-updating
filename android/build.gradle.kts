allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)

    // vosk_flutter_service 0.1.2 hard-codes compileSdk 33 in its own
    // android/build.gradle, while its AndroidX dependencies require API 34+.
    // Override only that plugin at configuration time so the library compiles
    // against the same modern SDK as the app without changing minSdk/targetSdk.
    if (name == "vosk_flutter_service") {
        afterEvaluate {
            val androidExtension = extensions.findByName("android")
                ?: throw GradleException("Vosk Android extension was not created")

            val compileSdkSetter = androidExtension.javaClass.methods.firstOrNull {
                it.name == "setCompileSdk" && it.parameterCount == 1
            }

            if (compileSdkSetter != null) {
                compileSdkSetter.invoke(androidExtension, 36)
            } else {
                val legacySetter = androidExtension.javaClass.methods.firstOrNull {
                    it.name == "compileSdkVersion" && it.parameterCount == 1
                } ?: throw GradleException(
                    "Could not override vosk_flutter_service compileSdk to 36",
                )

                val parameter = legacySetter.parameterTypes.single()
                val value: Any = if (parameter == String::class.java) "36" else 36
                legacySetter.invoke(androidExtension, value)
            }

            logger.lifecycle("Voice Ludo: vosk_flutter_service compileSdk forced to 36")
        }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
