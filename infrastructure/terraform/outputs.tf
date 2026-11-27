output "namespaces" {
  value = [kubernetes_namespace.app.metadata[0].name, kubernetes_namespace.monitoring.metadata[0].name]
}

output "database_secret" {
  description = "Name of the Secret that holds the database password (the value is not an output)"
  value       = "${kubernetes_secret.database.metadata[0].namespace}/${kubernetes_secret.database.metadata[0].name}"
}

output "pod_quota" {
  value = kubernetes_resource_quota.app.spec[0].hard["pods"]
}
