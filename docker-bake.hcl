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
  tags = [
    "wafflebot-file-downloader:${TAG}",
    "wafflebot-audio-mixer:${TAG}", 
    "wafflebot-publish-to-dropbox:${TAG}",
    "wafflebot-publish-podcast-to-s3:${TAG}",
    "wafflebot-update-rss-feed:${TAG}",
    "wafflebot:${TAG}"
  ]
}   