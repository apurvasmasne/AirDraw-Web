document.addEventListener('DOMContentLoaded', function () {
  let currentIndex = 0;
  const steps = document.querySelectorAll('.step');
  const totalSteps = steps.length;
  
  // Show the first step (image)
  showStep(currentIndex);

  function showStep(index) {
    // Hide all steps
    steps.forEach(step => {
      step.style.display = 'none';
      step.classList.remove('fade-in');
    });
    
    // Show the current step with fade-in effect
    steps[index].style.display = 'flex'; // Use flex to maintain layout
    setTimeout(() => {
      steps[index].classList.add('fade-in');
    }, 50); // Slight delay for fade effect
  }

  // Auto slide to the next step every 3 seconds
  setInterval(function () {
    currentIndex = (currentIndex + 1) % totalSteps;
    showStep(currentIndex);
  }, 3000);

  // Show the next step when the user clicks on the right arrow
  document.querySelector('.next-btn').addEventListener('click', function () {
    currentIndex = (currentIndex + 1) % totalSteps;
    showStep(currentIndex);
  });

  // Show the previous step when the user clicks on the left arrow
  document.querySelector('.prev-btn').addEventListener('click', function () {
    currentIndex = (currentIndex - 1 + totalSteps) % totalSteps;
    showStep(currentIndex);
  });

  // Video control logic
  const playButton = document.querySelector('.play-video-btn');
  const video = document.getElementById('airdraw-video');

  playButton.addEventListener('click', function () {
    video.style.display = 'block';  // Make the video visible
    video.style.opacity = 1;        // Fade in the video
    playButton.style.display = 'none';  // Hide the play button
    video.play();  // Start playing the video
  });
});
