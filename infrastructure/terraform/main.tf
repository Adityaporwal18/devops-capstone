terraform {
  required_version = ">= 1.6"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "kubernetes" {
  config_path    = pathexpand(var.kubeconfig)
  config_context = var.kube_context
}

resource "kubernetes_namespace" "app" {
  metadata {
    name   = var.app_namespace
    labels = { "app.kubernetes.io/part-of" = "eventhub" }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name   = var.monitoring_namespace
    labels = { "app.kubernetes.io/part-of" = "eventhub" }
  }
}

resource "kubernetes_resource_quota" "app" {
  metadata {
    name      = "eventhub-quota"
    namespace = kubernetes_namespace.app.metadata[0].name
  }
  spec {
    hard = {
      pods              = var.max_pods
      "requests.cpu"    = "2"
      "requests.memory" = "2Gi"
      "limits.memory"   = "3Gi"
    }
  }
}

resource "kubernetes_limit_range" "app" {
  metadata {
    name      = "eventhub-defaults"
    namespace = kubernetes_namespace.app.metadata[0].name
  }
  spec {
    limit {
      type            = "Container"
      default         = { memory = "192Mi" }
      default_request = { cpu = "25m", memory = "64Mi" }
    }
  }
}

resource "random_password" "database" {
  length  = 32
  special = false
}

resource "kubernetes_secret" "database" {
  metadata {
    name      = "eventhub-db"
    namespace = kubernetes_namespace.app.metadata[0].name
  }
  data = {
    POSTGRES_PASSWORD = random_password.database.result
    DATABASE_URL      = "postgresql://eventhub:${random_password.database.result}@eventhub-db:5432/eventhub"
  }
}
