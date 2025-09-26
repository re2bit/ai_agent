FROM ruby:3.2.9-alpine3.21

RUN apk add --no-cache \
    figlet \
    && gem install lolcat

CMD figlet -f big "        a        " | lolcat && \
    figlet -f mini "Local ai Dev environment" | lolcat