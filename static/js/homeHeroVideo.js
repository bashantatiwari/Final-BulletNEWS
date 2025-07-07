async function loadBreakingNewsVideo() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/get-latest-video/')
    const data = await response.json()
    document.getElementById('breaking-news-video').src = data.video_url
  } catch (err) {
    console.error('Failed to load video', err)
  }
}

// Load once on page load
loadBreakingNewsVideo()

// Auto-refresh every 10 minutes
setInterval(loadBreakingNewsVideo, 600000) // 10 min
