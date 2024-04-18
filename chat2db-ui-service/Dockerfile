FROM openjdk:18-jdk-alpine3.14

COPY ./chat2db-server-start.jar app.jar
COPY ./jdbc-lib /root/.chat2db/jdbc-lib

ENTRYPOINT ["java","-jar", "-Dserver.port=80", "/app.jar"]
