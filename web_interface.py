import streamlit as st
import os
import asyncio
import tempfile
import shutil
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import utility functions
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

# Configure Streamlit page
st.set_page_config(
    page_title="Text-to-Video AI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

def check_api_keys():
    """Check if required API keys are set"""
    missing_keys = []

    if not os.getenv('OPENAI_KEY') and not os.getenv('GROQ_API_KEY'):
        missing_keys.append("Either OPENAI_KEY or GROQ_API_KEY")
    if not os.getenv('PEXELS_KEY'):
        missing_keys.append("PEXELS_KEY")

    return missing_keys

def create_progress_bar():
    """Create a progress bar placeholder"""
    return st.progress(0)

def update_progress_bar(progress_bar, progress, status_text):
    """Update progress bar with status"""
    progress_bar.progress(progress)
    st.session_state.current_status = status_text

def generate_video_pipeline(topic, progress_bar):
    """Main video generation pipeline with progress tracking"""

    # Constants
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    st.info(f"🎬 Starting video generation pipeline for: '{topic}'")

    try:
        # Step 1: Generate script (15%)
        update_progress_bar(progress_bar, 0.15, "📝 Generating script from topic...")
        st.info("🤖 Calling AI to generate script...")
        script = generate_script(topic)
        st.session_state.generated_script = script
        st.success(f"✅ Script generated successfully! ({len(script)} characters)")

        # Step 2: Generate audio (30%)
        update_progress_bar(progress_bar, 0.30, "🎙️ Converting text to speech...")
        asyncio.run(generate_audio(script, SAMPLE_FILE_NAME))
        st.success("✅ Audio generated successfully!")

        # Step 3: Generate timed captions (45%)
        update_progress_bar(progress_bar, 0.45, "⏱️ Generating timed captions...")
        timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)
        st.session_state.timed_captions = timed_captions
        st.success("✅ Captions generated successfully!")

        # Step 4: Generate video search queries (60%)
        update_progress_bar(progress_bar, 0.60, "🔍 Creating video search queries...")
        search_terms = getVideoSearchQueriesTimed(script, timed_captions)
        st.session_state.search_terms = search_terms

        if search_terms is None:
            st.warning("⚠️ Could not generate video search queries")
            return None

        st.success("✅ Search queries generated!")

        # Step 5: Find background videos (75%)
        update_progress_bar(progress_bar, 0.75, "🎥 Finding background videos...")
        background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)

        if background_video_urls is None:
            st.warning("⚠️ No background videos found")
            return None

        st.success(f"✅ Found {len(background_video_urls)} background video segments!")

        # Step 6: Merge empty intervals (85%)
        update_progress_bar(progress_bar, 0.85, "🔧 Processing video segments...")
        background_video_urls = merge_empty_intervals(background_video_urls)

        # Step 7: Render final video (100%)
        update_progress_bar(progress_bar, 0.95, "🎬 Rendering final video...")
        video_path = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)

        update_progress_bar(progress_bar, 1.0, "✅ Video generation complete!")
        st.success("🎉 Video generated successfully!")

        return video_path

    except Exception as e:
        st.error(f"❌ Error during video generation: {str(e)}")
        return None
    finally:
        # Clean up temporary audio file
        if os.path.exists(SAMPLE_FILE_NAME):
            os.remove(SAMPLE_FILE_NAME)

def main():
    """Main Streamlit application"""

    # Header
    st.markdown('<h1 class="main-header">🎬 Text-to-Video AI</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar for API key status and settings
    with st.sidebar:
        st.header("🔧 Settings")

        # Check API keys
        missing_keys = check_api_keys()
        if missing_keys:
            st.error("❌ Missing API Keys:")
            for key in missing_keys:
                st.write(f"- {key}")
            st.info("Please set these environment variables and restart the app.")
        else:
            st.success("✅ All API keys configured!")

        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. Enter a topic for your video
        2. Click "Generate Video"
        3. Wait for processing
        4. Download your video!

        The process typically takes 2-5 minutes.
        """)

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🎥 Create Your Video")

        # Topic input
        topic = st.text_input(
            "Enter your video topic:",
            placeholder="e.g., Amazing space facts, Weird animal facts, Historical mysteries...",
            help="Enter a topic for a short, engaging video (under 50 seconds)"
        )

        # Example topics
        with st.expander("💡 Example Topics"):
            example_topics = [
                "Weird facts you don't know",
                "Amazing space discoveries",
                "Incredible animal abilities",
                "Historical mysteries solved",
                "Mind-blowing science facts",
                "Fascinating world records"
            ]

            for ex_topic in example_topics:
                if st.button(ex_topic, key=f"ex_{ex_topic}"):
                    st.session_state.topic_input = ex_topic
                    st.rerun()

        # Use session state for topic
        if 'topic_input' in st.session_state:
            topic = st.session_state.topic_input

        # Generate button
        if st.button("🎬 Generate Video", type="primary", disabled=not topic or len(missing_keys) > 0):
            if not topic.strip():
                st.error("Please enter a topic!")
                return

            st.info(f"🚀 Starting video generation for topic: '{topic.strip()}'")

            # Initialize session state
            st.session_state.generating = True
            st.session_state.current_status = "Starting video generation..."
            st.session_state.video_path = None
            st.rerun()

    with col2:
        st.header("📊 Status")

        # Show current status
        if 'generating' in st.session_state and st.session_state.generating:
            progress_bar = create_progress_bar()
            st.markdown(f"**Status:** {st.session_state.get('current_status', 'Initializing...')}")
        elif 'video_path' in st.session_state and st.session_state.video_path:
            st.success("✅ Video ready!")
            st.image("https://via.placeholder.com/300x200?text=Video+Ready", width=300)
        else:
            st.info("🎬 Enter a topic to get started!")

    # Generation section
    if 'generating' in st.session_state and st.session_state.generating:
        if not topic or not topic.strip():
            st.error("❌ No topic provided!")
            st.session_state.generating = False
            st.rerun()
            return

        st.info(f"🎥 Processing topic: '{topic.strip()}'")
        progress_bar = create_progress_bar()

        try:
            # Generate video
            video_path = generate_video_pipeline(topic.strip(), progress_bar)

            if video_path:
                st.session_state.video_path = video_path
                st.success("✅ Video generation completed!")
            else:
                st.error("❌ Video generation failed!")

            st.session_state.generating = False
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error during video generation: {str(e)}")
            st.session_state.generating = False
            st.rerun()

    # Display results
    if 'video_path' in st.session_state and st.session_state.video_path:
        st.header("🎉 Your Video is Ready!")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.video(st.session_state.video_path)

            # Download button
            with open(st.session_state.video_path, 'rb') as video_file:
                st.download_button(
                    label="📥 Download Video",
                    data=video_file.read(),
                    file_name=f"text_to_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4"
                )

        with col2:
            st.header("📋 Generated Content")

            # Show generated script
            if 'generated_script' in st.session_state:
                with st.expander("📝 Generated Script"):
                    st.text(st.session_state.generated_script)

            # Show video info
            if os.path.exists(st.session_state.video_path):
                file_size = os.path.getsize(st.session_state.video_path) / (1024 * 1024)  # MB
                st.metric("File Size", f"{file_size:.1f} MB")

            # Generate new video button
            if st.button("🆕 Generate New Video"):
                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()