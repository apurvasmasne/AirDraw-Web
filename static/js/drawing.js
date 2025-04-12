// Kalman Filter class for smoothing
class KalmanFilter {
    constructor(processNoise = 1, measurementNoise = 1, estimatedError = 1) {
        this.processNoise = processNoise;
        this.measurementNoise = measurementNoise;
        this.estimatedError = estimatedError;
        this.value = 0;
        this.errorCovariance = 1;
    }

    update(measurement) {
        // Prediction step
        const kalmanGain = this.errorCovariance / (this.errorCovariance + this.measurementNoise);
        this.value = this.value + kalmanGain * (measurement - this.value);  // Correct the estimate

        // Update the error covariance
        this.errorCovariance = (1 - kalmanGain) * this.errorCovariance + Math.abs(this.value) * this.processNoise;

        return this.value;
    }
}

// Bézier curve function
function calculateBezierPoint(p0, p1, p2, p3, t) {
    const u = 1 - t;
    const tt = t * t;
    const uu = u * u;
    const uuu = uu * u;
    const ttt = tt * t;

    const x = uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x;
    const y = uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y;

    return { x, y };
}

// Function to draw Bézier curve using points
function drawBezierCurve(points) {
    if (points.length < 4) return;

    const steps = 20; // Adjust this for smoother or less smooth curve
    context.beginPath();
    context.moveTo(points[0].x, points[0].y);

    for (let t = 0; t <= 1; t += 1 / steps) {
        const p = calculateBezierPoint(points[0], points[1], points[2], points[3], t);
        context.lineTo(p.x, p.y);
    }

    context.stroke();
}

// Function to smooth drawing path using Kalman filter
function smoothDrawing(x, y) {
    const smoothedX = kalmanX.update(x);
    const smoothedY = kalmanY.update(y);
    return { smoothedX, smoothedY };
}

// Initialize Kalman filter for x and y axes
const kalmanX = new KalmanFilter();
const kalmanY = new KalmanFilter();

// Canvas setup
const canvas = document.querySelector('canvas');
const context = canvas.getContext('2d');
let drawing = false;
let points = []; // Stores the last 4 points for Bézier curves

canvas.addEventListener('mousedown', (e) => {
    drawing = true;
    points = []; // Clear points when starting a new drawing
});

canvas.addEventListener('mouseup', () => {
    drawing = false;
});

canvas.addEventListener('mousemove', (e) => {
    if (!drawing) return;

    const mouseX = e.offsetX;
    const mouseY = e.offsetY;

    // Apply Kalman filter to smooth coordinates
    const { smoothedX, smoothedY } = smoothDrawing(mouseX, mouseY);

    // Add smoothed point to the points array
    points.push({ x: smoothedX, y: smoothedY });

    // Keep only the last 4 points for Bézier curve
    if (points.length > 4) {
        points.shift();
    }

    // If we have 4 points, draw the Bézier curve
    if (points.length === 4) {
        drawBezierCurve(points);
    }

    // Continue drawing the line
    context.lineTo(smoothedX, smoothedY);
    context.stroke();
});

canvas.addEventListener('mouseout', () => {
    if (drawing) {
        drawing = false;
    }
});



// Function to clear the canvas
function clearCanvas() {
    if (confirm('Are you sure you want to clear the canvas?')) {
        fetch('/clear_canvas', { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    alert('Failed to clear the canvas.');
                }
            });
    }
}

// Function to save the canvas
function saveCanvas() {
    fetch('/save_canvas', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                return response.text();
            } else {
                throw new Error('Failed to save the canvas.');
            }
        })
        .then(filePath => {
            alert('Canvas saved as ' + filePath);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Could not save canvas.');
        });
}

// Function to highlight the selected color box
function highlightSelectedColor(index) {
    const colorBoxes = document.querySelectorAll('.color-box');
    colorBoxes.forEach((box, i) => {
        box.style.border = i === index ? '2px solid black' : 'none';
    });
}

let selectedColorIndex = 0;  // Default selected color (red)

// Function to select a color and update the backend
function selectColor(index) {
    selectedColorIndex = index;  // Update selected color index

    // Send the selected color to the Flask backend
    fetch('/set_color/' + index, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            highlightSelectedColor(index);  // Highlight selected color
            alert('Color selected: ' + colors[index]);
        } else {
            alert('Failed to change color.');
        }
    });
}

// Function to initialize the page
window.onload = function () {
    highlightSelectedColor(0);
};
