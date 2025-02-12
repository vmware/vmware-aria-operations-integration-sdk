import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    id("java")
    kotlin("jvm") version "1.9.0"
    kotlin("plugin.serialization") version "1.9.0"
    id("org.jetbrains.dokka") version "1.9.0"
    id("io.github.gradle-nexus.publish-plugin") version "2.0.0-rc-2"
    `java-library`
    `signing`
    `maven-publish`
}

group = "com.vmware.aria.operations"
version = "1.1.0"

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(17))
    }
}

repositories {
    mavenCentral()
}

val ktorVersion = "2.3.3"

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.9.2"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.junit.jupiter:junit-jupiter-params")
    testImplementation("org.wiremock:wiremock:3.1.0")
    testImplementation("org.slf4j:slf4j-simple:2.0.9")

    implementation(kotlin("stdlib-jdk8"))
    implementation("io.ktor:ktor-serialization-kotlinx-json:$ktorVersion")
    implementation("io.ktor:ktor-client-core:$ktorVersion")
    implementation("io.ktor:ktor-client-cio:$ktorVersion")
    implementation("io.ktor:ktor-client-content-negotiation:$ktorVersion")
    api("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.1")
    api("org.apache.logging.log4j:log4j-core:2.20.0")
    api("org.apache.logging.log4j:log4j-api:2.20.0")
}

tasks.test {
    useJUnitPlatform()
}

val javadocJar by tasks.creating(Jar::class) {
    group = JavaBasePlugin.DOCUMENTATION_GROUP
    description = "Assembles Javadoc JAR"
    archiveClassifier.set("javadoc")
    from(tasks.named("dokkaHtml"))
}

nexusPublishing {
    repositories {
        sonatype()
    }
}

publishing {
    publications {
        create<MavenPublication>("mavenJava") {
            from(components["java"])
            artifact(tasks.kotlinSourcesJar.get())
            artifact(javadocJar)
            pom {
                name.set("VMware Aria Operations Integration SDK Adapter Libraray")
                description.set("A library for facilitating the development of Adapters using the VMware Cloud Foundation Operations Integration SDK")
                url.set("https://github.com/vmware/vmware-aria-operations-integration-sdk")
                licenses {
                    license {
                        name.set("The Apache License, Version 2.0")
                        url.set("http://www.apache.org/licenses/LICENSE-2.0.txt")
                    }
                }
                developers {
                    developer {
                        id.set("kjrokos")
                        name.set("Kyle Rokos")
                        email.set("kyle.rokos@broadcom.com")
                    }
                }
                scm {
                    connection.set("scm:git:git://github.com/vmware/vmware-aria-operations-integration-sdk.git")
                    developerConnection.set("scm:git:ssh://github.com/vmware/vmware-aria-operations-integration-sdk.git")
                    url.set("https://github.com/vmware/vmware-aria-operations-integration-sdk/tree/main")
                }
            }
        }
    }
}

signing {
    sign(publishing.publications["mavenJava"])
}
