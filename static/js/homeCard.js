document.querySelectorAll('.headline-of-the-news').forEach((el) => {
  const fullText = el.textContent.trim()
  const limit = 50
  if (fullText.length > limit) {
    el.textContent = fullText.slice(0, limit) + '..'
    el.setAttribute('title', fullText) // optional: show full on hover
  }
})
