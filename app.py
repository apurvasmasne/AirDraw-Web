from flask import Flask, render_template, redirect, url_for, request, flash, session, Response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import cv2
import numpy as np
import mediapipe as mp
from collections import deque

# Initialize the Flask app
app = Flask(__name__)


# Configure the app and SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite database for simplicity
app.config['SECRET_KEY'] = 'your_secret_key'  # To protect sessions
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthenticated users to login page

# User Model for SQLAlchemy
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# User loader function (required by Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Load the user by their ID

# Initialize MediaPipe Hands
mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=2, min_detection_confidence=0.7)  # Detect up to 2 hands

camera = cv2.VideoCapture(0)
camera_running = True  # Flag to control camera state

# Color points
bpoints = [deque(maxlen=1024)]
gpoints = [deque(maxlen=1024)]
rpoints = [deque(maxlen=1024)]
ypoints = [deque(maxlen=1024)]
# New color points for additional colors
blackpoints = [deque(maxlen=1024)]
whitepoints = [deque(maxlen=1024)]
cyanpoints = [deque(maxlen=1024)]
pinkpoints = [deque(maxlen=1024)]
orangepoints = [deque(maxlen=1024)]

colors = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (0, 0, 0),      # Black
    (255, 255, 255), # White
    (0, 255, 255),  # Cyan
    (255, 0, 255),  # Pink
    (128, 0, 128),   # Purple
    (174, 198, 207),  # Pastel Blue
    (255, 0, 0),      # Bright Red
    (128, 128, 0),    # Olive Green
    (211, 211, 211),  # Light Grey
    (255, 215, 0),    # Gold
    (230, 230, 250),  # Lavender
    (25, 25, 112)     # Midnight Blue
]
next_color_index = 0  # Default color (red)

current_line = []
lines = []
bpoints = [deque(maxlen=1024)]  # Store points for drawing
last_gesture_was_open_palm = False

# Generate frames for video feed
def generate_frames():
    global next_color_index, last_gesture_was_open_palm, camera_running, current_line
    width, height = 640, 480  # Dimensions for the canvas
    border_thickness = 5  # Thickness of the border

    while camera_running:  # Check camera_running flag
        success, frame = camera.read()
        if not success:
            break
        
        # Create a blank white canvas
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
        
        # Draw the border
        cv2.rectangle(canvas, (0, 0), (width, height), (0, 0, 0), border_thickness)  # Black border

        # Process the camera frame for hand detection
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(framergb)

        if result.multi_hand_landmarks:
            for handslms in result.multi_hand_landmarks:
                landmarks = []
                for lm in handslms.landmark:
                    lmx = int(lm.x * width)
                    lmy = int(lm.y * height)
                    landmarks.append([lmx, lmy])
                
                # Draw all landmarks (0 to 20) as small black circles, mirrored
                for lm in landmarks:
                    mirrored_x = width - lm[0]  # Mirror the x-coordinate
                    cv2.circle(canvas, (mirrored_x, lm[1]), 5, (0, 0, 0), -1)  # Black circles for landmarks

                # Draw lines between the landmarks to visualize the palm shape
                for i in range(21):  # Connect all landmarks
                    if i < 20:  # Ensure we don't go out of bounds
                        cv2.line(canvas, (width - landmarks[i][0], landmarks[i][1]),
                                 (width - landmarks[i + 1][0], landmarks[i + 1][1]), (0, 0, 0), 1)

            # Check if an open palm is detected
            if len(result.multi_hand_landmarks) == 1:
                fingers_up = [
                    landmarks[8][1] < landmarks[6][1],  # Index finger
                    landmarks[12][1] < landmarks[10][1],  # Middle finger
                    landmarks[16][1] < landmarks[14][1],  # Ring finger
                    landmarks[20][1] < landmarks[18][1]   # Pinky
                ]
                current_gesture_is_open_palm = all(fingers_up)

                # Change color only if the gesture changed to open palm
                if current_gesture_is_open_palm and not last_gesture_was_open_palm:
                    next_color_index = (next_color_index + 1) % len(colors)

                last_gesture_was_open_palm = current_gesture_is_open_palm

            # Check if a victory sign is made with one hand
            if len(result.multi_hand_landmarks) == 1 and \
                abs(landmarks[8][1] - landmarks[12][1]) < 30 and \
                (landmarks[4][1] - landmarks[8][1]) > 30:
                # Save the current line and start a new one
                if current_line:
                    lines.append((current_line, next_color_index))  # Store current line and its color
                    current_line = []

            # Only draw if the index finger is straight
            if len(result.multi_hand_landmarks) == 1 and landmarks[8][1] < landmarks[4][1]:  # Index finger is straight
                current_line.append(tuple(landmarks[8]))
            else:
                # Save the current line if the index finger is not detected
                if current_line:
                    lines.append((current_line, next_color_index))  # Store current line and its color
                    current_line = []

        # Draw the current line while it's being drawn
        if current_line:
            for i in range(1, len(current_line)):
                cv2.line(canvas, (width - current_line[i - 1][0], current_line[i - 1][1]),
                         (width - current_line[i][0], current_line[i][1]),
                         colors[next_color_index], 2)

        # Draw all lines that have been drawn so far
        for line, color_index in lines:
            for i in range(1, len(line)):
                cv2.line(canvas, (width - line[i - 1][0], line[i - 1][1]),
                         (width - line[i][0], line[i][1]),
                         colors[color_index], 2)

        # Convert the canvas to a JPEG format suitable for streaming
        ret, buffer = cv2.imencode('.jpg', canvas)
        if not ret:
            break
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# All routes

# Route to process the saved drawing

@app.route('/set_color/<int:index>', methods=['POST'])
def set_color(index):
    global next_color_index
    # Ensure the index is within the valid range of color indices
    if 0 <= index < len(colors):
        next_color_index = index  # Update the color index
        return '', 200  # Success response
    else:
        return 'Invalid color index', 400  # Error response

lines = []  # For storing drawn lines
last_gesture_was_open_palm = False  # Track if the last gesture was an open palm

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Using the default method, which is 'pbkdf2_sha256'
        hashed_password = generate_password_hash(password)  # This uses pbkdf2_sha256 by default
        
        # Check if the user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!", "danger")
            return redirect(url_for('signup'))

        # Add new user to the database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Find the user by username
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)  # Login the user with Flask-Login
            flash("Logged in successfully!", "success")
            return redirect(url_for('drawing'))  # Redirect to drawing page

        flash("Invalid username or password!", "danger")
        return redirect(url_for('login'))
    
    return render_template('login.html')

# Drawing route (After login)
@app.route('/drawing', methods=['GET', 'POST'])
@login_required
def drawing():
    return render_template('drawing.html')

# Logout route
@app.route('/logout')
def logout():
    logout_user()  # Logout the user with Flask-Login
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

# Stream the video feed
@app.route('/stream')
def stream():
    print("Mew")
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/clear_canvas', methods=['POST'])  
def clear_canvas():
    global lines
    lines = []  # Clear the lines stored
    return '', 204  # No content response to indicate success

@app.route('/save_canvas', methods=['POST'])
def save_canvas():
    global lines
    if not lines:
        return '', 204  # No content to save
    
    # Create a blank canvas
    height, width = 480, 640
    canvas = np.zeros((height, width, 3), dtype=np.uint8)

    # Draw all lines on the canvas
    for line, color_idx in lines:
        for i in range(1, len(line)):
            cv2.line(canvas, line[i - 1], line[i], colors[color_idx], 2)

    # Save the canvas to a file
    save_path = 'saved_canvas.png'
    cv2.imwrite(save_path, canvas)

    return save_path, 200  # Return the path of the saved file

# Initialize the database inside the Flask app context
def init_db():
    with app.app_context():
        db.create_all()  # Create all database tables

if __name__ == "__main__":
    init_db()  # Initialize the database
    app.run(debug=True)
