plugins {
    kotlin("android") version "1.9.22"
    id("com.android.application") version "8.2.0"
    application
}

repositories {
    google()
    mavenCentral()
}

dependencies {
    implementation(kotlin("stdlib"))
    implementation("com.badlogicgames.gdx:gdx:1.12.0")
    implementation("com.badlogicgames.gdx:gdx-backend-lwjgl3:1.12.0")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-desktop")

    // Android backend
    implementation("com.badlogicgames.gdx:gdx-backend-android:1.12.0")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-armeabi")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-armeabi-v7a")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-arm64-v8a")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-x86")
    implementation("com.badlogicgames.gdx:gdx-platform:1.12.0:natives-x86_64")
}

android {
    namespace = "com.boardrockchess"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.boardrockchess"
        minSdk = 21
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}

application {
    mainClass.set("com.boardrockchess.MainKt")
}

kotlin {
    jvmToolchain(17)
}
