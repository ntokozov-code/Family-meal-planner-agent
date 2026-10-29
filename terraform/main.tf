# Infrastructure as Code (IaC) - Terraform configuration for Cloud Deployment
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "GCP Project ID for deploying the meal planning agent"
  default     = "meal-agent-prod"
}

variable "region" {
  type        = string
  description = "Target deployment cloud region"
  default     = "us-central1"
}

resource "google_cloud_run_v2_service" "meal_agent_service" {
  name     = "family-meal-concierge-agent"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/family-meal-planner-agent:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "gemini-api-key"
            version = "latest"
          }
        }
      }
    }
  }
}

output "service_url" {
  value       = google_cloud_run_v2_service.meal_agent_service.uri
  description = "Publicly accessible endpoint of deployed Meal Agent"
}
