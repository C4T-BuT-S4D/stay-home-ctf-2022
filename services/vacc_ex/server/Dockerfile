FROM adoptopenjdk/openjdk16:debianslim as build
WORKDIR /tmp/gradle/compile
COPY gradle ./gradle
COPY *.gradle ./
COPY gradlew ./
COPY src ./src
RUN ./gradlew --no-daemon build && ls -al

FROM adoptopenjdk/openjdk16:debianslim-jre
WORKDIR /app
COPY --from=build /tmp/gradle/compile/build/libs/* .
ENTRYPOINT ["java", "-jar", "/app/exchange-all.jar"]