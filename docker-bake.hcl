variable "TAG" {
  default = "latest"
}

group "default" {
  targets = ["wafflebot"]
}

group "all" {
  targets = ["wafflebot"]
}

target "wafflebot" {
  dockerfile = "Dockerfile"
  context = "."
  tags = ["wafflebot:${TAG}"]
}   