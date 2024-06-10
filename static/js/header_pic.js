document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('change-picture-btn').addEventListener('click', function() {
      var images = [
        '/static/css/images/aboutme/alex0.png',
        '/static/css/images/aboutme/alex1.png',
        '/static/css/images/aboutme/alex2.png',
        '/static/css/images/aboutme/alex5.png'
      ];

      var currentImageSrc = document.getElementById('profile-picture').src.split('/').pop();
      var currentImageIndex = images.map(function(image) { return image.split('/').pop(); }).indexOf(currentImageSrc);
      
      var nextImageIndex = (currentImageIndex + 1) % images.length;
      
      document.getElementById('profile-picture').src = images[nextImageIndex];
  });
});

//-----------------------------
document.addEventListener('DOMContentLoaded', () => {
    const players = document.querySelectorAll('.player');
    let currentIndex = 0;

    function showPlayer(index) {
        players.forEach((player, i) => {
            player.classList.toggle('active', i === index);
        });
    }

    document.getElementById('prev').addEventListener('click', () => {
        currentIndex = (currentIndex === 0) ? players.length - 1 : currentIndex - 1;
        showPlayer(currentIndex);
    });

    document.getElementById('next').addEventListener('click', () => {
        currentIndex = (currentIndex === players.length - 1) ? 0 : currentIndex + 1;
        showPlayer(currentIndex);
    });

    // Initially show the first player
    showPlayer(currentIndex);
});

