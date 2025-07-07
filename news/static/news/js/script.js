document.addEventListener('DOMContentLoaded', function () {
  // Initialize featured news for each category
  initializeCategories()

  // Add click event listener to all headline cards
  const headlineCards = document.querySelectorAll('.headline-card')
  headlineCards.forEach((card) => {
    card.addEventListener('click', function () {
      // Get the category and article index data attributes
      const category = this.dataset.category
      const articleIndex = this.dataset.articleIndex

      if (!category) return // Skip if no category data

      // Remove active class from all cards in this category
      const categoryCards = document.querySelectorAll(
        `.headline-card[data-category="${category}"]`
      )
      categoryCards.forEach((c) => c.classList.remove('active'))

      // Add active class to the clicked card
      this.classList.add('active')

      // Update the featured article content based on the clicked article
      updateFeaturedArticle(this)

      // Optional: Scroll to make sure the featured content is visible
      const featuredContainer = this.closest(
        '.category-container'
      ).querySelector('.featured-container')
      if (featuredContainer) {
        featuredContainer.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        })
      }
    })
  })

  // Function to update the featured article content
  function updateFeaturedArticle(headlineCard) {
    // Get all the data from the headline card
    const { category, image, title, author, date, body, readTime } =
      headlineCard.dataset

    // Find the featured container for this category
    const featuredCard = document.getElementById(`featured-${category}`)
    if (!featuredCard) return

    // Update the featured card with the new content
    const featuredImage = featuredCard.querySelector('.featured-image img')
    if (featuredImage && image) {
      featuredImage.src = image
      featuredImage.alt = title || ''
    }

    const featuredTitle = featuredCard.querySelector('.featured-title')
    if (featuredTitle) {
      featuredTitle.textContent = title || ''
    }

    const featuredAuthor = featuredCard.querySelector('.featured-author')
    if (featuredAuthor) {
      featuredAuthor.textContent = author || ''
    }

    const featuredDate = featuredCard.querySelector('.featured-date')
    if (featuredDate) {
      featuredDate.textContent = date || ''
    }

    const featuredBody = featuredCard.querySelector('.featured-body')
    if (featuredBody && body) {
      // Parse HTML content safely
      featuredBody.innerHTML = body
    }

    const readTimeEl = featuredCard.querySelector('.read-time')
    if (readTimeEl) {
      readTimeEl.textContent = readTime || ''
    }

    // Animate the transition
    featuredCard.style.opacity = '0.7'
    setTimeout(() => {
      featuredCard.style.opacity = '1'
    }, 300)
  }

  // Function to highlight the first news article in each category by default
  function initializeCategories() {
    const categories = document.querySelectorAll('.category-feed-section')
    categories.forEach((category) => {
      const firstHeadline = category.querySelector('.headline-card')
      if (firstHeadline) {
        firstHeadline.classList.add('active')
      }
    })
  }

  // Optional: Add infinite scroll for headlines if needed
  let isLoading = false

  function loadMoreNews(categoryName) {
    if (isLoading) return

    isLoading = true

    // Here you would typically make an AJAX request to fetch more news
    // For demonstration, we'll simulate a loading delay

    // Example AJAX request structure:
    /*
      fetch(`/api/news/${categoryName}?page=${nextPage}`)
          .then(response => response.json())
          .then(data => {
              // Append new articles to the list
              const headlinesList = document.querySelector(`[data-category="${categoryName}"] .headlines-list`);
              data.articles.forEach(article => {
                  // Create and append new article elements
              });
              isLoading = false;
          })
          .catch(error => {
              console.error('Error loading more news:', error);
              isLoading = false;
          });
      */

    // Simulate request completion after 1 second
    setTimeout(() => {
      isLoading = false
    }, 1000)
  }

  // Optional: Implement scroll detection for each category's headline list
  const scrollableSections = document.querySelectorAll('.scrollable-content')
  scrollableSections.forEach((section) => {
    section.addEventListener('scroll', function () {
      // If we're near the bottom, load more content
      if (this.scrollTop + this.clientHeight >= this.scrollHeight - 200) {
        const categorySection = this.closest('.category-feed-section')
        const categoryName = categorySection
          .querySelector('.section-title')
          .textContent.trim()
        loadMoreNews(categoryName)
      }
    })
  })

  // Make the "Read More" links work
  const readMoreLinks = document.querySelectorAll('.read-more-link')
  readMoreLinks.forEach((link) => {
    link.addEventListener('click', function (e) {
      e.preventDefault()
      // In a real app, this would navigate to the full article page
      // For now, just show the full article body by removing max-height
      const featuredBody = this.closest('.featured-news-card').querySelector(
        '.featured-body'
      )
      if (featuredBody) {
        if (featuredBody.style.maxHeight) {
          featuredBody.style.maxHeight = ''
          this.textContent = 'Show Less'
        } else {
          featuredBody.style.maxHeight = '400px'
          this.textContent = 'Read More'
        }
      }
    })
  })
})
