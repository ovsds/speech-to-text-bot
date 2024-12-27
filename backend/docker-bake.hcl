variable "IMAGE_REGISTRY" {}
variable "IMAGE_NAME" { default = "speech-to-text-bot" }
variable "IMAGE_TAG" {}

target "base" {
  dockerfile = "Dockerfile"
  contexts = {
    "base_builder" = "docker-image://docker.io/library/python:3.12.7-bookworm"
    "base_runtime" = "docker-image://docker.io/library/python:3.12.7-slim-bookworm"
    "sources" = "."
  }
}

target "runtime" {
  inherits = ["base"]
  target = "runtime"
  tags = ["${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"]
  output = ["type=image,push=true"]
  platforms = [
    "linux/amd64",
    "linux/arm64",
  ]
  attest = [
    "type=provenance,mode=max",
    "type=sbom",
  ]
  annotations = [
  ]
}

target "runtime_dev" {
  inherits = ["base"]
  target = "runtime_dev"
  output = ["type=docker"]
  tags = ["${IMAGE_NAME}:runtime"]
}

target "tests_dev" {
  inherits = ["base"]
  target = "tests_dev"
  output = ["type=docker"]
  tags = ["${IMAGE_NAME}:tests"]
}
