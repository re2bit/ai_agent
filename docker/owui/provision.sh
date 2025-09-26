#!/usr/bin/env bash
set -e

function showHelp() {
    echo ""
    echo "provision - provision scripts for open-webui"
    echo "usage: startup COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "➖➖➖➖➖➖➖➖➖"
    echo "⚪  h,    help                    This Help" # Check
    echo "⚪  ca,   create-admin            Creates a Admin User" # Check
    echo "⚪  cp,   create-pipeline         Creates Ollama Pipeline" # Check

    echo ""
    echo "➖➖➖➖➖➖➖➖➖"
    echo "‼️Hint: add functionality to this Script"
    echo ""
}

function provision() {
    case $1 in
        ca|create-admin)
            shift
            createAdmin "$@"
            ;;
        cp|create-pipeline)
            shift
            createPipeline "$@"
            ;;
        h|help)
            shift
            showHelp "$@"
            ;;
        *)
            echo -e "\033[31m'$1' is not a known Command.\033[0m"
            showHelp
            echo ""
            ;;
    esac
}

function createAdmin() {
    if [[ "$1" == "--help" ]]; then
      echo "usage: provision [ca|create-admin] [ALEMBIC_COMMAND] [ALEMBIC_OPTIONS]"
      echo ""
      echo "Run Alembic migrations commands in the agent-server(as) container."
      echo ""
      echo "Examples:"
      echo "  a m upgrade head                       # Upgrade to the latest migration"
      echo "  a migrations revision --autogenerate -m \"description\"  # Create a new migration"
      echo "  a m history                            # Show migration history"
      echo "  a m current                            # Show current migration version"
      echo ""
      exit 1
  fi


  local admin_email
  local admin_password
  local secret
  admin_email="$1"
  admin_password="$2"
  secret="$3"

   if [ ! "$admin_email" ] || [  ! "$admin_password" ]; then
     echo "e-mail and password are required"
     exit 1
  fi

  echo "Starting Server..."
  WEBUI_SECRET_KEY="$secret" uvicorn open_webui.main:app --host "localhost" --port "8080" --forwarded-allow-ips '*' &
  webui_pid=$!
  echo "Waiting for Server to start..."
  while ! curl -s http://localhost:8080/health > /dev/null; do
    echo "Waiting for Server to start... may take while due to a download"
    sleep 1
  done
  echo "Creating admin user..."
  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "http://localhost:8080/api/v1/auths/signup" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{ \"email\": \"${admin_email}\", \"password\": \"${admin_password}\", \"name\": \"Admin\" }" \
    || true)

  case "$response" in
    201)
      echo "Admin erfolgreich angelegt."
      ;;
    400|409)
      echo "Admin gibt es schon."
      ;;
    *)
      echo "Signup fehlgeschlagen. HTTP-Code: $response"
      ;;
  esac
  echo "Shutting down webui..."
  kill $webui_pid
  sleep 1
}

function createPipeline() {
  if [[ "$1" == "--help" ]]; then
    echo "usage: provision [cp|create-pipeline] [ADMIN_EMAIL] [ADMIN_PASSWORD]"
    echo ""
    echo "Waits till the Server is Up, Logs in with admin credentials, Creates Pipeline configuration."
    echo ""
    echo "Examples:"
    echo "  provision cp admin@ai.de toor          # Create pipeline with admin credentials"
    echo ""
    exit 1
  fi

  local admin_email
  local admin_password
  admin_email="$1"
  admin_password="$2"

  if [ ! "$admin_email" ] || [ ! "$admin_password" ]; then
    echo "Admin e-mail and password are required"
    exit 1
  fi

  echo "Waiting for Server to start..."
  if ! timeout 300 sh -c 'while ! curl -s http://localhost:8080/health > /dev/null; do echo "Waiting for Server to start..."; sleep 1; done'; then
    echo "❌ Timeout: Server did not start within 300 seconds."
    exit 1
  fi
  echo "Server is up!"

  echo "Logging in with admin credentials..."
  local login_response
  local token
  login_response=$(curl -s \
    -X POST "http://localhost:8080/api/v1/auths/signin" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -d "{ \"email\": \"${admin_email}\", \"password\": \"${admin_password}\" }")

  token=$(echo "$login_response" | grep -o '"token":"[^"]*' | cut -d'"' -f4)


  if [ -z "$token" ]; then
    echo "❌ Failed to login. Response:"
    echo "$login_response"
    exit 1
  fi

  echo "Successfully logged in and obtained token."
  echo "Token is ${token}"

 echo "Creating Ollama Pipeline configuration..."
  curl \
    -X POST "http://open-webui:8080/ollama/config/update" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${token}" \
    -d '{
      "ENABLE_OLLAMA_API": true,
      "OLLAMA_BASE_URLS": [
          "http://host.docker.internal:11434"
      ],
      "OLLAMA_API_CONFIGS": {
          "0": {
              "enable": true,
              "tags": [],
              "prefix_id": "",
              "model_ids": [],
              "connection_type": "external"
          }
      }
    }'

  echo "Creating OpenAI (Pipelines) configuration..."
  curl \
    -X POST "http://open-webui:8080/openai/config/update" \
    -H "accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${token}" \
    -d '{
      "ENABLE_OPENAI_API": true,
      "OPENAI_API_BASE_URLS": [
          "http://pipelines:9099"
      ],
      "OPENAI_API_KEYS": [
          "0p3n-w3bu!"
      ],
      "OPENAI_API_CONFIGS": {
          "0": {
              "enable": true,
              "tags": [],
              "prefix_id": "",
              "model_ids": [],
              "connection_type": "external"
          }
      }
    }'
}

if [ "$1" != "include" ]; then
  provision "$@"
fi
