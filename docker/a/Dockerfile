FROM alpine:latest

RUN apk add --no-cache \
    figlet \
    ruby \
    ruby-dev \
    && gem install lolcat

CMD figlet -f big "        a        " | lolcat && \
    figlet -f mini "Local ai Dev environment" | lolcat