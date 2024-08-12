import streamlit as st
import sqlite3
from PIL import Image
import base64

# Initialize connection to SQLite database
conn = sqlite3.connect('farmers.db')
c = conn.cursor()

# Create table for users
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, password TEXT)''')

# Create table for posts
c.execute('''CREATE TABLE IF NOT EXISTS posts
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, content TEXT, image BLOB, allow_comments INTEGER, FOREIGN KEY(user_id) REFERENCES users(id))''')

# Create table for comments
c.execute('''CREATE TABLE IF NOT EXISTS comments
             (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, user_id INTEGER, content TEXT, FOREIGN KEY(post_id) REFERENCES posts(id), FOREIGN KEY(user_id) REFERENCES users(id))''')

# Create table for videos
c.execute('''CREATE TABLE IF NOT EXISTS videos
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)''')

# Create table for news
c.execute('''CREATE TABLE IF NOT EXISTS news
             (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, content TEXT)''')

# Create table for messages
c.execute('''CREATE TABLE IF NOT EXISTS messages
             (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, receiver_id INTEGER, message TEXT, FOREIGN KEY(sender_id) REFERENCES users(id), FOREIGN KEY(receiver_id) REFERENCES users(id))''')

# Commit changes and close connection
conn.commit()
conn.close()

def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    signup_link = st.markdown("<style>a:hover{color:red;}</style> <a href='signup'>Don't have an account? Sign Up</a>", unsafe_allow_html=True)

    if st.button("Login", key="login_btn"):
        conn = sqlite3.connect('farmers.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE name=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            st.success(f"Logged in as {username}")
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
        else:
            st.error("Invalid username or password")

def signup():
    st.subheader("Sign Up")
    name = st.text_input("Name", key="signup_name")
    phone = st.text_input("Phone Number", key="signup_phone")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
    login_link = st.markdown("<style>a:hover{color:red;}</style> <a href='login'>Already have an account? Login</a>", unsafe_allow_html=True)

    if st.button("Sign Up", key="signup_btn"):
        if password != confirm_password:
            st.error("Passwords do not match")
        else:
            conn = sqlite3.connect('farmers.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name, phone, password) VALUES (?, ?, ?)", (name, phone, password))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            st.success("Sign Up successful")
            st.session_state.logged_in = True
            st.session_state.user_id = user_id

def view_profile(user_id):
    conn = sqlite3.connect('farmers.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()

    st.subheader(f"Profile: {user[1]}")
    st.write(f"Phone: {user[2]}")

    # Display messages
    st.subheader("Messages")
    c.execute("SELECT u.name, m.message FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.receiver_id = ?", (user_id,))
    messages = c.fetchall()

    if not messages:
        st.write("No messages yet.")
    else:
        for message in messages:
            st.write(f"**{message[0]}**: {message[1]}")

    # Display user's posts
    st.subheader("Your Posts")
    c.execute("SELECT p.id, p.content, p.image, p.allow_comments FROM posts p WHERE p.user_id = ?", (user_id,))
    user_posts = c.fetchall()
    conn.close()  # Close the connection after fetching data

    if not user_posts:
        st.write("You haven't made any posts yet.")
    else:
        for post in user_posts:
            st.write(f"**Post ID: {post[0]}**")
            if post[2]:  # If the post has an image
                st.image(post[2], use_column_width=True, caption=post[1])
            else:  # If the post is text-only
                st.write(post[1])

            if post[3]:  # If comments are allowed for this post
                st.write("**Comments:**")
                display_comments(post[0])

            st.write("---")


def create_post(user_id):
    st.subheader("Create Post")
    post_type = st.radio("Post Type", ["Text", "Image"])
    allow_comments = st.checkbox("Allow Comments", value=True)

    if post_type == "Text":
        content = st.text_area("Post Content")

        if st.button("Post", key="text_post_btn"):
            if not content:
                st.error("Post content cannot be empty")
            else:
                conn = sqlite3.connect('farmers.db')
                c = conn.cursor()
                c.execute("INSERT INTO posts (user_id, content, allow_comments) VALUES (?, ?, ?)", (user_id, content, allow_comments))
                conn.commit()  # Commit changes
                conn.close()  # Close the connection
                st.success("Post created successfully")
                # Refresh the page to update the posts section
                st.experimental_rerun()

    elif post_type == "Image":
        caption = st.text_area("Image Caption")
        uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

        if st.button("Post", key="image_post_btn"):
            if not caption:
                st.error("Image caption cannot be empty")
            elif not uploaded_file:
                st.error("You must upload an image")
            else:
                conn = sqlite3.connect('farmers.db')
                c = conn.cursor()
                image = uploaded_file.read()
                c.execute("INSERT INTO posts (user_id, content, image, allow_comments) VALUES (?, ?, ?, ?)", (user_id, caption, image, allow_comments))
                conn.commit()  # Commit changes
                conn.close()  # Close the connection
                st.success("Post created successfully")
                # Refresh the page to update the posts section
                st.experimental_rerun()

def view_posts():
    st.subheader("Posts")
    conn = sqlite3.connect('farmers.db')
    c = conn.cursor()
    c.execute("SELECT p.id, u.name, p.content, p.image, p.allow_comments FROM posts p JOIN users u ON p.user_id = u.id")
    posts = c.fetchall()
    conn.close()  # Close the connection after fetching data

    if not posts:
        st.write("No posts yet.")
    else:
        for post in posts:
            st.write(f"**{post[1]}**")
            if post[3]:  # If the post has an image
                st.image(post[3], use_column_width=True, caption=post[2])
            else:  # If the post is text-only
                st.write(post[2])

            if post[4]:  # If comments are allowed for this post
                st.write("**Comments:**")
                display_comments(post[0])

            st.write("---")
        st.write("---")

def display_comments(post_id):
    conn = sqlite3.connect('farmers.db')
    c = conn.cursor()
    c.execute("SELECT u.name, c.content FROM comments c JOIN users u ON c.user_id = u.id WHERE c.post_id = ?", (post_id,))
    comments = c.fetchall()
    conn.close()

    if not comments:
        st.write("No comments yet.")
    else:
        for comment in comments:
            st.write(f"**{comment[0]}**: {comment[1]}")

    add_comment(post_id)

def add_comment(post_id):
    comment = st.text_input("Add a comment", key=f"comment_{post_id}")
    if st.button("Submit Comment", key=f"submit_comment_{post_id}"):
        if not comment:
            st.error("Comment cannot be empty")
        else:
            conn = sqlite3.connect('farmers.db')
            c = conn.cursor()
            c.execute("INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)", (post_id, st.session_state.user_id, comment))
            conn.commit()
            conn.close()
            st.success("Comment added successfully")

def view_videos():
    st.subheader("Videos")
    
    # Define CSS styles for video container
    st.markdown(
        """
        <style>
            .video-container {
                margin-bottom: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }
            .video-container iframe {
                width: 100%;
                height: 315px; /* Adjust height as needed */
                border: none;
            }
            .video-title {
                background-color: #f4f4f4;
                padding: 10px;
                font-size: 18px;
                border-bottom: 1px solid #ddd;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                color:#000;
                font-family:times-new-roman;
                test-transform:uppercase;
                font-weight:bold;
                content-align:center;
            }
        
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Define a list of YouTube video titles and corresponding URLs
    video_info = [
        ("THE HISTORY OF FARMING", "https://www.youtube.com/embed/xFqecEtdGZ0"),
        ("THE FUTURE OF FARMING", "https://www.youtube.com/embed/Qmla9NLFBvU"),
        ("THE SCIENCE BEHIND FARMING", "https://www.youtube.com/embed/LGF33NN4B8U"),
        ("ORGANIC FARMING", "https://www.youtube.com/embed/WhOrIUlrnPo"),
        ("THE PROS AND CONS OF ORGANIC FARMING", "https://www.youtube.com/embed/QpkKW45cHaA"),
        ("THE IMPORTANCE OF AGRICULTURE", "https://www.youtube.com/embed/UE8fQm_DxI4"),
        ("TECH IN FARMING", "https://www.youtube.com/embed/mYdt6CAwKAY"),
        ("THE FARMERS JOURNEY ", "https://www.youtube.com/embed/LTSZomX8vXo"),
        ("SUSTAINABLE FARMING", "https://www.youtube.com/embed/5SzJkL7czI0"),
        ("SUSTAINABLE AGRICULTURE", "https://www.youtube.com/embed/iloAQmroRK0"),
        ("FARMING USING AI", "https://www.youtube.com/embed/JeU_EYFH1Jk"),
        
        # Add more video titles and URLs here...
    ]

    # Loop through each video info tuple and display the video
    for title, url in video_info:
        st.write(f"<div class='video-container'><div class='video-title'>{title}</div><iframe src={url} frameborder='0' allowfullscreen></iframe></div>", unsafe_allow_html=True)

def view_news():
    st.subheader("News")
    # Define a list of news articles with titles and content
    news_articles = [
         ("TODAY'S WEATHER", "CLICK HERE TO KNOW MORE [More](https://www.timeanddate.com/weather/india/tamil-nadu)."),
         ("Wheat stocks in govt warehouses at 16-year low after record sales", "Indian wheat stocks held in government warehouses dropped to their lowest level in 16 years after two straight years of reduced crop yields prompted New Delhi to sell record volumes to boost domestic supplies and bring down local prices. [Read More](https://www.business-standard.com/industry/agriculture/wheat-stocks-in-govt-warehouses-at-16-year-low-after-record-sales-124041900742_1.html)."),
        ("Plant sensors could act as an early warning system for farmers", "Using a pair of sensors made from carbon nanotubes, researchers discovered signals that help plants respond to stresses such as heat, light, or attack from insects or bacteria. Farmers could use these sensors to monitor threats to their crops, allowing them to intervene before the crops are lost. [Read More](https://www.sciencedaily.com/releases/2024/04/240417131057.htm)."),
        ("Signs of change in rural economy", "The state of consumption, especially in the rural economy, has become akin to a riddle ever since the second wave of the Covid-19 pandemic. Multiple shocks, and that too in quick succession, have only added to the chaos.  [Read More](https://www.financialexpress.com/opinion/signs-of-change-in-rural-economy/3462531/)."),
        ("Forecast of good monsoon brightens farm prospects", "India will likely reap a bumper harvest in the next crop year starting July, as monsoon rains are projected to be bountiful with a good geographical spread, [Read More](https://economictimes.indiatimes.com/news/economy/agriculture/forecast-of-good-monsoon-brightens-farm-prospects/articleshow/109443240.cms?from=mdr)."),
        ("India's wheat stocks hit 16-year low as record sales, free distribution raise supply concerns", "Despite the sharp fall in stocks, the government was able to meet the buffer and strategic reserve norms that mandate holding wheat stocks at or above 7.46 million mt April 1. [Read More ](https://www.spglobal.com/commodityinsights/en/market-insights/latest-news/agriculture/041924-indias-wheat-stocks-hit-16-year-low-as-record-sales-free-distribution-raise-supply-concerns)."),
        ("New govt may kick off pesticide, seed reforms in agriculture sector", "With farm Acts out of the picture, the government may look at reforming the input side of the agriculture sector — regulations and rules that govern seeds, fertilisers and plant chemicals [Read More ](https://www.business-standard.com/economy/news/govt-might-look-at-reforming-agri-inputs-administration-in-next-tenure-124041700690_1.html)."),
        ("India's pulses import almost doubled in 2023-24, it may rise further this year", "Despite several measures, including various incentives to farmers, India is still dependent on imports of pulses for its domestic requirements. [Read More ](https://economictimes.indiatimes.com/news/economy/agriculture/indias-pulses-import-almost-doubled-in-2023-24-it-may-rise-further-this-year/articleshow/109361102.cms?from=mdr)."),
        
        # Add more news articles here...
    ]

    # Loop through each news article tuple and display it
    for title, content in news_articles:
        st.write(f"**{title}**")
        st.write(content)
        st.write("---")


def send_message(sender_id, receiver_id):
    st.subheader("Send Message")
    message = st.text_area("Message")

    if st.button("Send"):
        if not message:
            st.error("Message cannot be empty")
        else:
            conn = sqlite3.connect('farmers.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (sender_id, receiver_id, message))
            conn.commit()
            conn.close()
            st.success("Message sent successfully")

def home_page(user_id):
    """App home function"""
    st.title("Farmers Hub")

    menu = ["Profile", "Posts", "Videos", "News", "Create Post"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Profile":
        view_profile(user_id)
        recipient_username = st.text_input("Enter recipient's username", key="message_username")
        message = st.text_area("Message", key="message_content")

        if st.button("Send Message"):
            conn = sqlite3.connect('farmers.db')
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE name = ?", (recipient_username,))
            recipient = c.fetchone()
            conn.close()

            if recipient:
                recipient_id = recipient[0]
                conn = sqlite3.connect('farmers.db')
                c = conn.cursor()
                c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (user_id, recipient_id, message))
                conn.commit()
                conn.close()
                st.success(f"Message sent to {recipient_username}")
            else:
                st.error("Invalid username. Please try again.")

    elif choice == "Posts":
        view_posts()
    elif choice == "Videos":
        view_videos()
    elif choice == "News":
        view_news()
    elif choice == "Create Post":
        create_post(user_id)

if __name__ == '__main__':
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None

    if not st.session_state.logged_in:
        login_choice = st.sidebar.radio("Login/Signup", ["Login", "Signup"])

        if login_choice == "Login":
            login()
        elif login_choice == "Signup":
            signup()
    else:
        home_page(st.session_state.user_id)
