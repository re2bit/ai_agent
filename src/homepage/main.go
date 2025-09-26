package main

import (
	"embed"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
)

//go:embed templates/index.html
var templateFS embed.FS

type ServiceLink struct {
	Name string
	URL  string
}

type PageData struct {
	ServiceLinks []ServiceLink
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}


	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		var serviceLinks []ServiceLink
		
		if port := os.Getenv("AGENT_SERVER_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "Agent Server",
				URL:  fmt.Sprintf("http://localhost:%s/docs", port),
			})
		}

		if port := os.Getenv("PIPELINES_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "Pipelines Server",
				URL:  fmt.Sprintf("http://localhost:%s/docs", port),
			})
		}
		
		if port := os.Getenv("LANGFUSE_WEB_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "Langfuse Web",
				URL:  fmt.Sprintf("http://localhost:%s", port),
			})
		}
		
		if port := os.Getenv("OWUI_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "Open WebUI",
				URL:  fmt.Sprintf("http://localhost:%s", port),
			})
		}

		if port := os.Getenv("SEARXNG_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "SearxNG",
				URL:  fmt.Sprintf("http://localhost:%s", port),
			})
		}
		
		// Link to mitmproxy Web UI (direct, not via reverse proxy)
		if port := os.Getenv("MITMPROXY_WEB_PORT_PUBLIC"); port != "" {
			serviceLinks = append(serviceLinks, ServiceLink{
				Name: "mitmproxy Web UI",
				URL:  fmt.Sprintf("http://localhost:%s/", port),
			})
		}
		
		tmpl, err := template.ParseFS(templateFS, "templates/index.html")
		if err != nil {
			log.Printf("Error parsing template: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		data := PageData{
			ServiceLinks: serviceLinks,
		}

		err = tmpl.Execute(w, data)
		if err != nil {
			log.Printf("Error executing template: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
	})

	fmt.Printf("Server starting on port %s...\n", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}