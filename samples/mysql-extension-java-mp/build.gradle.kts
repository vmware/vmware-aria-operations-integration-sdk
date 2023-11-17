/*
 * Copyright 2023 VMware, Inc.
 * SPDX-License-Identifier: Apache-2.0
 */

plugins {
    java
}

tasks.register<Copy>("generateDependencies") {
    from(configurations.runtimeClasspath.get())
    into("${rootProject.projectDir}/dependencies")
}

sourceSets {
    main {
        java.setSrcDirs(listOf("src"))
    }
}

tasks.named<Jar>("jar") {
    dependsOn("generateDependencies")
    manifest {
        attributes["Adapter"] = "com.vmware.aria.operations.adapters.mysqlextension.Adapter"
    }
}

dependencies {
    implementation("com.vmware.aria.operations:integration-sdk-adapter-library:1.0.2")
    implementation("mysql:mysql-connector-java:8.0.33")

}

repositories {
    mavenCentral()
}


