FROM node:14.17.0-alpine
ENV EVENT_BUS_NAME=SANDBOX-EventCentral
ENV SCHEMA_REGISTRY_NAME=discovered-schemas
ENV REGION=us-west-2
ENV BUCKET_NAME=sandbox-eventbridge-atla-eventbridgeatlassandboxb-zldk8q04pzmr
COPY ./stacks/atlas_stacks/bin ./app
WORKDIR /app
RUN npm install
RUN apk update && apk add --no-cache chromium
RUN apk add --no-cache bash
CMD ["npm", "run", "build:asyncapi"]