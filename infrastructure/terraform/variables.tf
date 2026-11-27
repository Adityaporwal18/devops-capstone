variable "kubeconfig" {
  description = "Path of the kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Kubernetes context of the platform cluster"
  type        = string
  default     = "capstone"
}

variable "app_namespace" {
  description = "Namespace of the EventHub application"
  type        = string
  default     = "eventhub"
}

variable "monitoring_namespace" {
  description = "Namespace of the monitoring and logging stack"
  type        = string
  default     = "monitoring"
}

variable "max_pods" {
  description = "Largest number of pods allowed in the application namespace"
  type        = number
  default     = 20
}
