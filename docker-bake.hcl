variable "TAG" {
  default = "latest"
}

group "default" {
  targets = ["all"]
}

group "all" {
  targets = [
    "file-downloader",
    "audio-mixer", 
    "publish-to-dropbox",
    "publish-podcast-to-s3",
    "update-rss-feed"
  ]
}

target "wafflebot-base" {
  dockerfile = "Dockerfile"
  context = "."
  target = "base"
  tags = ["wafflebot-base:latest"]
}

target "file-downloader" {
  dockerfile = "Dockerfile"
  context = "."
  target = "file-downloader"
  tags = ["wafflebot-file-downloader:${TAG}"]
}

target "audio-mixer" {
  dockerfile = "Dockerfile"
  context = "."
  target = "audio-mixer"
  tags = ["wafflebot-audio-mixer:${TAG}"]
}

target "publish-to-dropbox" {
  dockerfile = "Dockerfile"
  context = "."
  target = "publish-to-dropbox"
  tags = ["wafflebot-publish-to-dropbox:${TAG}"]
}

target "publish-podcast-to-s3" {
  dockerfile = "Dockerfile"
  context = "."
  target = "publish-podcast-to-s3"
  tags = ["wafflebot-publish-podcast-to-s3:${TAG}"]
}

target "update-rss-feed" {
  dockerfile = "Dockerfile"
  context = "."
  target = "update-rss-feed"
  tags = ["wafflebot-update-rss-feed:${TAG}"]
} 