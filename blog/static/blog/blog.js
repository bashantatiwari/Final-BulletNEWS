document.addEventListener('DOMContentLoaded', () => {
  // Dynamic Featured Section
  const featuredSection = document.querySelector('.featured-section')
  const featuredContent = document.querySelector('.featured-content')
  const posts = document.querySelectorAll('.blog-page-card')
  let currentIndex = 0

  function updateFeaturedPost() {
    if (posts.length > 0) {
      const post = posts[currentIndex]
      const imgSrc = post
        .querySelector('.card-image')
        .style.backgroundImage.slice(5, -2) // Extract URL
      const category = post.querySelector('.category').textContent
      const title = post.querySelector('.title').textContent
      const author = post.querySelector('.author').textContent
      const date = post.querySelector('.date').textContent

      featuredSection.style.backgroundImage = `url('${imgSrc}')`
      featuredContent.querySelector('.category').textContent = category
      featuredContent.querySelector('.title').textContent = title
      featuredContent.querySelector('.author').textContent = author
      featuredContent.querySelector('.date').textContent = date

      currentIndex = (currentIndex + 1) % posts.length
    }
  }

  setInterval(updateFeaturedPost, 5000) // Change every 5 seconds
  updateFeaturedPost() // Initial call

  // Load More Functionality
  const loadMoreBtn = document.getElementById('loadMore')
  const hiddenCards = document.querySelectorAll('.hidden-card')
  let visibleCount = 3

  loadMoreBtn.addEventListener('click', () => {
    const cardsToShow = Array.from(hiddenCards).slice(0, 3) // Show 3 more
    cardsToShow.forEach((card) => card.classList.remove('hidden-card'))
    visibleCount += cardsToShow.length
    if (visibleCount >= posts.length) loadMoreBtn.style.display = 'none'
  })
})
