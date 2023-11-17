# First Stage: Build the Java project using Gradle
FROM gradle:8.3.0-jdk17 AS build

# Set the working directory inside the Docker image
WORKDIR /home/gradle/project

# Copy the Gradle build file and the source code
COPY build.gradle.kts .
COPY src src

# Run Gradle to compile the code
RUN gradle build

# If the harbor repo isn't accessible, the base-adapter image can be built locally.
# Go to the vmware-aria-operations-integration-sdk repository, and run the build_images.py script located at images/build_images.py
FROM projects.registry.vmware.com/vmware_aria_operations_integration_sdk/base-adapter:java-1.0.0
COPY commands.cfg .
WORKDIR /home/aria-ops-adapter-user/src/app

# Copy the compiled jar from the build stage and its dependencies
COPY --from=build /home/gradle/project/build/libs/*.jar app.jar
COPY --from=build /home/gradle/project/dependencies dependencies
