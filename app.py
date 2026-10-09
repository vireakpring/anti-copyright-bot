import asyncio
import os
import re
import subprocess
import edge_tts
from moviepy import (
    AudioFileClip,
    CompositeAudioClip,
    VideoFileClip,
    concatenate_videoclips,
    vfx,
)
import streamlit as st
import whisper
import yt_dlp

# ---------------------------------------------------------
# 1. INITIALIZATION & PROFESSIONAL YELLOW THEME STYLING
# ---------------------------------------------------------
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "output"
TEMP_DIR = "temp_web"

for folder in [DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(folder, exist_ok=True)

st.set_page_config(
    page_title="Professional Video Processing & AI Dubbing Studio",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Yellow Theme CSS Styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFFDE7;
        max-width: 1280px;
        margin: 0 auto;
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        background-color: #FFF59D;
        padding: 24px;
        border-radius: 8px;
        border: 2px solid #FBC02D;
        margin-bottom: 24px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .title-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E65100;
        margin-bottom: 4px;
    }
    .subtitle-text {
        font-size: 0.95rem;
        color: #4E342E;
    }
    [data-testid="stSidebar"] {
        background-color: #FFF9C4;
        border-right: 1px solid #FBC02D;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 3.2em;
        font-weight: 600;
        background-color: #F57F17;
        color: #FFFFFF;
        border: none;
    }
    .stButton>button:hover {
        background-color: #E65100;
        color: #FFFFFF;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
        <div class="title-text">Video Processing & AI Dubbing Studio (ប្រព័ន្ធកាត់តវីដេអូ និងបកប្រែសំឡេង AI)</div>
        <div class="subtitle-text">Automated Video Obfuscation, Whisper Transcription & Multi-lingual AI Voice Generation</div>
    </div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. HELPER FUNCTIONS & ENGINES
# ---------------------------------------------------------


def download_video_from_url(url: str, output_path: str):
    """Download video from URL using yt-dlp with player client spoofing"""
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_path,
        "overwrites": True,
        "quiet": True,
        "no_warnings": True,
        "color": "no_color",
        "nocheckcertificate": True,
        "geo_bypass": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        },
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


async def generate_edge_tts(
    text: str, voice: str, pitch_str: str, rate_str: str, out_path: str
):
    """Generate Edge-TTS Audio File"""
    communicate = edge_tts.Communicate(
        text, voice, pitch=pitch_str, rate=rate_str
    )
    await communicate.save(out_path)


@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")


def analyze_video_whisper(v_path: str, lang: str, status_box) -> str:
    """Extract audio and transcribe text using local Whisper AI"""
    status_box.info("Whisper AI: Transcribing audio / កំពុងបម្លែងសំឡេងទៅជាអត្ថបទ...")
    model = load_whisper_model()
    audio_temp = os.path.join(TEMP_DIR, "extracted_audio.mp3")

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        v_path,
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-ab",
        "128k",
        audio_temp,
    ]
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    task_type = "translate" if "English" in lang else "transcribe"
    result = model.transcribe(audio_temp, task=task_type)

    script_lines = []
    for segment in result.get("segments", []):
        start = round(segment["start"], 2)
        end = round(segment["end"], 2)
        text = segment["text"].strip()
        if text:
            script_lines.append(f"({start} - {end}) {text}")

    return "\n".join(script_lines)


def apply_anti_copyright_filter(
    input_mp4: str,
    final_output_mp4: str,
    mute_audio: bool,
    resolution: str,
    fps: int,
    status_box,
):
    """Apply visual obfuscation filter via FFmpeg"""
    status_box.info("FFmpeg Engine: Applying Anti-Copyright filter / កំពុងរត់ Filter ផ្តាច់ Copyright...")

    scale_res = (
        "scale=1920:1080" if resolution == "1080p (Full HD)" else "scale=1280:720"
    )

    vf_chain = (
        "hflip,"
        "crop=in_w*0.88:in_h*0.88,"
        f"{scale_res},"
        "eq=brightness=0.04:contrast=1.12:saturation=1.15:gamma=1.05,"
        "setpts=PTS/1.06"
    )

    cmd = ["ffmpeg", "-y", "-i", input_mp4, "-vf", vf_chain]

    if mute_audio:
        cmd.extend(["-an"])
    else:
        af_chain = "atempo=1.06,volume=0.9"
        cmd.extend(["-af", af_chain, "-c:a", "aac", "-b:a", "192k"])

    cmd.extend(
        [
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-preset",
            "fast",
            final_output_mp4,
        ]
    )

    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        st.error(f"FFmpeg Execution Error / បរាជ័យ FFmpeg:\n{e.stderr}")
        raise e


# ---------------------------------------------------------
# 3. SIDEBAR CONTROL PANEL
# ---------------------------------------------------------
with st.sidebar:
    st.header("Configurations (ការកំណត់)")

    st.subheader("AI Voice Config (កំណត់សំឡេង AI)")
    target_lang = st.selectbox(
        "Target Voice Language (ភាសា AI និយាយ)",
        options=["ភាសាខ្មែរ (Khmer)", "English"],
    )

    if "Khmer" in target_lang or "ខ្មែរ" in target_lang:
        voice_dict = {
            "Piseth - Male (ពិសិដ្ឋ - ប្រុស)": "km-KH-PisethNeural",
            "Sreymom - Female (ស្រីមុំ - ស្រី)": "km-KH-SreymomNeural",
        }
    else:
        voice_dict = {
            "Guy - Male (ប្រុស)": "en-US-GuyNeural",
            "Aria - Female (ស្រី)": "en-US-AriaNeural",
            "Christopher - Narrative (រឿងនិទាន)": "en-US-ChristopherNeural",
        }

    selected_voice_label = st.selectbox(
        "Select Voice Model (ជ្រើសរើសសំឡេង)", options=list(voice_dict.keys())
    )
    selected_voice = voice_dict[selected_voice_label]

    st.markdown("---")
    st.subheader("Voice Tuning (សារេ Pitch និងល្បឿន)")
    tts_speed = st.slider("Speech Rate / ល្បឿននិយាយ", -20, 50, 0, step=5, format="%d%%")
    tts_pitch = st.slider("Pitch / កម្រិតស្រួច-ក្រាស់", -20, 20, 0, step=2, format="%dHz")

    speed_str = f"{'+' if tts_speed >= 0 else ''}{tts_speed}%"
    pitch_str = f"{'+' if tts_pitch >= 0 else ''}{tts_pitch}Hz"

    st.markdown("---")
    st.subheader("Export Options (ការកំណត់វីដេអូចេញ)")
    output_res = st.selectbox(
        "Output Resolution (ទំហំវីដេអូ)",
        options=["1080p (Full HD)", "720p (HD)"],
        index=0,
    )
    output_fps = st.selectbox("Frame Rate (FPS)", options=[24, 30, 60], index=1)

# ---------------------------------------------------------
# 4. MAIN CONTENT WORKFLOW (TABS)
# ---------------------------------------------------------
tab_video, tab_mode, tab_export = st.tabs(
    ["1. Video Source (ប្រភពវីដេអូ)", "2. Processing Options (ការកំណត់កាត់ត)", "3. Render Output (ទាញយកវីដេអូ)"]
)

video_input_path = os.path.join(DOWNLOAD_DIR, "input_video.mp4")
video_ready = False

with tab_video:
    st.subheader("Video Input Source (ជ្រើសរើសប្រភពវីដេអូ)")
    source_type = st.radio(
        "Select Input Method (វិធីសាស្ត្របញ្ចូលវីដេអូ):",
        ("Paste Video Link / បញ្ចូល Link", "Upload Video File Direct / Upload File ផ្ទាល់"),
        horizontal=True,
    )

    if "Link" in source_type:
        v_link = st.text_input("Video URL (Paste Link YouTube/TikTok/Facebook):")
        if v_link and st.button("Fetch Video (ទាញយកវីដេអូ)"):
            with st.spinner("Downloading video stream / កំពុងទាញយកវីដេអូ..."):
                try:
                    if os.path.exists(video_input_path):
                        os.remove(video_input_path)
                    download_video_from_url(v_link, video_input_path)
                    st.success("Video fetched successfully / ទាញយកវីដេអូជោគជ័យ!")
                except Exception as e:
                    clean_err = str(e).replace("[0;31mERROR:[0m", "").strip()
                    st.error(f"Download Error / បរាជ័យទាញយក: {clean_err}")

        if os.path.exists(video_input_path):
            st.video(video_input_path)
            video_ready = True
    else:
        uploaded_file = st.file_uploader(
            "Upload MP4 or MOV File:", type=["mp4", "mov"]
        )
        if uploaded_file is not None:
            with open(video_input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.video(video_input_path)
            video_ready = True

user_script = ""

with tab_mode:
    st.subheader("Processing Configuration (ការកំណត់ Mode កាត់ត)")

    col_opt1, col_opt2 = st.columns(2)

    with col_opt1:
        visual_processing = st.radio(
            "Visual Editing Mode (រូបភាពវីដេអូ):",
            (
                "Keep Original Video / រក្សារូបភាពវីដេអូដើម",
                "Apply Anti-Copyright Filter / រត់ Filter ផ្តាច់ Copyright",
            ),
        )

    with col_opt2:
        audio_handling = st.radio(
            "Original Audio Strategy (សំឡេងដើម):",
            (
                "Mute Original Audio / បិទសំឡេងដើមចោល 100%",
                "Keep Original Audio / រក្សាសំឡេងដើម (Mix ជាមួយ AI)",
            ),
        )

    st.markdown("---")
    st.subheader("Dubbing Strategy (ជម្រើសនៃការបញ្ចូលសំឡេង AI)")

    script_mode = st.radio(
        "Script Source (ប្រភព Script និយាយ):",
        (
            "Manual Script Entry / សរសេរ Timestamp Script ដោយខ្លួនឯង",
            "Whisper AI Auto-Transcription / ឱ្យ AI ស្ដាប់ និងបង្កើត Script ស្វ័យប្រវត្តិ",
            "No Dubbing / មិនបញ្ចូលសំឡេង AI (កាត់ត/រត់ Filter តែរូបភាព)",
        ),
    )

    if "Manual" in script_mode:
        user_script = st.text_area(
            "Timestamp Script Input / បញ្ចូល Script (Format: (start - end) text):",
            height=180,
            placeholder="(0 - 5) សួស្តីអ្នកទាំងអស់គ្នា!\n(5 - 12) Welcome to this automated video processing platform.",
        )

with tab_export:
    st.subheader("Render Pipeline (ដំណើរការ Render វីដេអូ)")
    btn_process = st.button("Start Processing Pipeline (ចាប់ផ្ដើមកាត់ត)")
    status_box = st.empty()


# ---------------------------------------------------------
# 5. EXECUTION PIPELINE
# ---------------------------------------------------------


def execute_pipeline():
    if not video_ready or not os.path.exists(video_input_path):
        st.error("Error: Please upload or fetch a video first / សូម Upload ឬ ទាញយកវីដេអូជាមុនសិន!")
        return None

    apply_filter = "Anti-Copyright Filter" in visual_processing
    mute_audio = "Mute Original Audio" in audio_handling

    script_text = user_script

    # Case 1: Whisper AI Auto Transcription
    if "Whisper AI" in script_mode:
        script_text = analyze_video_whisper(
            video_input_path, target_lang, status_box
        )
        if not script_text.strip():
            st.warning("Whisper AI did not detect speech / មិនជួបសំឡេងនិយាយក្នុងវីដេអូទេ!")
            out_file = os.path.join(OUTPUT_DIR, "processed_video.mp4")
            if apply_filter:
                apply_anti_copyright_filter(
                    video_input_path, out_file, mute_audio, output_res, output_fps, status_box
                )
            else:
                out_file = video_input_path
            return out_file

        st.success("Generated Transcript / Script ដែល AI ស្ដាប់បាន៖")
        st.code(script_text, language="text")

    # Case 2: Direct Processing without dubbing
    elif "No Dubbing" in script_mode or not script_text.strip():
        out_file = os.path.join(OUTPUT_DIR, "processed_video.mp4")
        if apply_filter:
            apply_anti_copyright_filter(
                video_input_path, out_file, mute_audio, output_res, output_fps, status_box
            )
            status_box.success("Anti-Copyright transformation completed / កាត់ផ្តាច់ Copyright ជោគជ័យ!")
            return out_file
        else:
            st.info("No editing or dubbing selected / គ្មានការកាត់ត ឬបកប្រែត្រូវបានជ្រើសរើសឡើយ។")
            return video_input_path

    # Dubbing Pipeline (Manual or Whisper Generated Script)
    status_box.info("Processing scenes and synthesizing AI narration / កំពុងកាត់ត និងបង្កើតសំឡេង AI...")
    lines = [line.strip() for line in script_text.split("\n") if line.strip()]
    video_clip = VideoFileClip(video_input_path)
    final_clips = []

    pattern = r"\(\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*\)\s*(.*)"

    for idx, line in enumerate(lines):
        match = re.search(pattern, line)
        if match:
            start_t = float(match.group(1))
            end_t = float(match.group(2))
            text = match.group(3).strip()

            if start_t < video_clip.duration:
                end_t = min(end_t, video_clip.duration)
                sub_video = video_clip.subclipped(start_t, end_t)

                if mute_audio:
                    sub_video = sub_video.without_audio()

                if text:
                    audio_file = os.path.join(TEMP_DIR, f"tts_{idx}.mp3")
                    asyncio.run(
                        generate_edge_tts(
                            text,
                            selected_voice,
                            pitch_str,
                            speed_str,
                            audio_file,
                        )
                    )

                    ai_audio_clip = AudioFileClip(audio_file)

                    if ai_audio_clip.duration > sub_video.duration:
                        speed_factor = (
                            sub_video.duration / ai_audio_clip.duration
                        )
                        sub_video = sub_video.with_effects(
                            [vfx.MultiplySpeed(speed_factor)]
                        )

                    if not mute_audio and sub_video.audio is not None:
                        combined_audio = CompositeAudioClip(
                            [sub_video.audio.volumex(0.15), ai_audio_clip]
                        )
                        sub_video = sub_video.with_audio(combined_audio)
                    else:
                        sub_video = sub_video.with_audio(ai_audio_clip)

                final_clips.append(sub_video)

    if not final_clips:
        st.error("Error: Could not parse timestamp script formatting / មិនអាចអានទម្រង់ Timestamp Script បានឡើយ!")
        video_clip.close()
        return None

    temp_synced_path = os.path.join(TEMP_DIR, "synced_temp.mp4")
    final_video = concatenate_videoclips(final_clips)
    final_video.write_videofile(
        temp_synced_path, codec="libx264", audio_codec="aac", fps=output_fps
    )

    video_clip.close()
    final_video.close()

    final_out_file = os.path.join(OUTPUT_DIR, "final_dubbed_studio_output.mp4")

    if apply_filter:
        apply_anti_copyright_filter(
            temp_synced_path,
            final_out_file,
            mute_audio=False,
            resolution=output_res,
            fps=output_fps,
            status_box=status_box,
        )
    else:
        final_out_file = temp_synced_path

    status_box.success("Processing completed successfully / កាត់ត និងបញ្ចូលសំឡេង AI ជោគជ័យ!")
    return final_out_file


if btn_process:
    result_video = execute_pipeline()
    if result_video and os.path.exists(result_video):
        st.subheader("Final Processed Output (វីដេអូលទ្ធផលចុងក្រោយ)")
        with open(result_video, "rb") as f:
            st.video(f.read())