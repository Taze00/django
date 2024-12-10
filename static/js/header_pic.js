document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('change-picture-btn').addEventListener('click', function() {
        var images = [
          '/static/css/images/aboutme/alex0.png',
          '/static/css/images/aboutme/alex2.png',
          '/static/css/images/aboutme/alex5.png'
        ];
  
        var currentImageSrc = document.getElementById('profile-picture').src.split('/').pop();
        var currentImageIndex = images.map(function(image) { return image.split('/').pop(); }).indexOf(currentImageSrc);
        
        var nextImageIndex = (currentImageIndex + 1) % images.length;
        
        document.getElementById('profile-picture').src = images[nextImageIndex];
    });
  });
  
  
