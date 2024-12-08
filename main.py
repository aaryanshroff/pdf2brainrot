import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from gtts import gTTS
import nltk
from nltk.tokenize import word_tokenize
from pydub import AudioSegment
import google.generativeai as genai

# --------------------- Configuration ---------------------
SCRIPT_PATH = 'script.txt'         # Path to your script file
BACKGROUND_VIDEO = 'background.mov'  # Path to your background video
VOICEOVER_AUDIO = 'voiceover.mp3'    # Output path for the generated voiceover
FINAL_VIDEO = 'final_video.mp4'       # Output path for the final video
FPS = 24                              # Frames per second for the output video
FONT = 'Arial-Bold.ttf'                   # Font type for text
FONT_SIZE = 40                        # Font size for text
TEXT_COLOR = 'white'                  # Text color
TEXT_POSITION = ('center', 'top')   # Position of the text
BG_OPACITY = 0.5                       # Opacity for text background

PROMPT_TEMPLATE = """
Create a concise and engaging script for a TikTok-style video explaining the topic: {topic}. The script should be approximately 60 seconds long and include the following elements:

1. **Hook**: Start with an attention-grabbing question or statement to pique viewers' interest.
2. **Introduction**: Briefly introduce the topic.
3. **Key Points**: Highlight 3-5 important facts or concepts about the topic, presenting them in a simple and easy-to-understand manner.
4. **Analogies or Examples**: Use relatable analogies or examples to clarify complex ideas.
5. **Conclusion**: End with a summary or a thought-provoking statement.
6. **Call-to-Action**: Encourage viewers to like, follow, or engage with the content for more information.

Ensure the language is clear, conversational, and suitable for a broad audience. Avoid technical jargon unless it's explained simply. Keep the tone upbeat and motivating to maintain viewer engagement throughout the video. No headings or special formatting (including emojis).
"""

# --------------------------------------------------------
GEMINI_API_KEY=os.environ["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")
topic = input("Enter topic:")
prompt = PROMPT_TEMPLATE.format(topic=topic)
script = model.generate_content(prompt).text


# --------------------- Setup NLTK -------------------------
# Download NLTK's Punkt tokenizer if not already downloaded
nltk.download('punkt')
# --------------------------------------------------------

# --------------------- Step 1: Generate Voiceover ---------------

# Generate voiceover using gTTS
tts = gTTS(text=script, lang='en')
tts.save(VOICEOVER_AUDIO)
print("Voiceover audio generated.")

# Load the audio to get duration
audio = AudioSegment.from_mp3(VOICEOVER_AUDIO)
audio_duration = audio.duration_seconds  # in seconds
print(f"Voiceover Duration: {audio_duration} seconds")
# -------------------------------------------------------------

# --------------------- Step 2: Load Background Video --------------
# Load the background video
background = VideoFileClip(BACKGROUND_VIDEO)
print(f"Background video loaded: {BACKGROUND_VIDEO}")
# ---------------------------------------------------------------

# --------------------- Step 3: Load Voiceover Audio ----------------
# Load the voiceover audio
voiceover = AudioFileClip(VOICEOVER_AUDIO)
print(f"Voiceover audio loaded: {VOICEOVER_AUDIO}")
# ----------------------------------------------------------------

# --------------------- Step 4: Adjust Video Duration -----------------
# Ensure the background video matches the voiceover duration
if background.duration < voiceover.duration:
    # Loop the background video if it's shorter than the voiceover
    background = background.loop(duration=voiceover.duration)
    print("Background video looped to match voiceover duration.")
elif background.duration > voiceover.duration:
    # Trim the background video if it's longer than the voiceover
    background = background.subclipped(0, voiceover.duration)
    print("Background video trimmed to match voiceover duration.")
else:
    print("Background video and voiceover durations match.")
# -----------------------------------------------------------------

# --------------------- Step 5: Split Script into Words -----------------
# Tokenize the script into words for synchronized text display
words = word_tokenize(script)
num_words = len(words)
print(f"Total Words: {num_words}")

# Calculate per-word duration
per_word_duration = audio_duration / num_words
print(f"Per-Word Duration: {per_word_duration} seconds")
# -------------------------------------------------------------------

# --------------------- Step 6: Create Text Clips ---------------------
text_clips = []
for i, word in enumerate(words):
    start_time = i * per_word_duration
    # Remove any newline characters from words
    word_clean = word.replace('\n', ' ')
    # Create a TextClip for each word
    txt_clip = TextClip(
        text=word_clean,
        font_size=FONT_SIZE,
        color=TEXT_COLOR,
        font=FONT,
        bg_color=f'rgba(0,0,0,{int(BG_OPACITY * 255)})',  # Semi-transparent background
        method='label'
    ).with_position(TEXT_POSITION).with_start(start_time).with_duration(per_word_duration)
    
    text_clips.append(txt_clip)
    print(f"Text clip created for word {i+1}: \"{word_clean}\"")
# -------------------------------------------------------------------

# --------------------- Step 7: Combine All Text Clips ----------------
# Combine all TextClips into a single CompositeVideoClip
all_text = CompositeVideoClip(text_clips, size=background.size).with_duration(background.duration)
print("All text clips combined.")
# ---------------------------------------------------------------------

# --------------------- Step 8: Combine Video and Audio ----------------
# Set the voiceover audio to the background video
video_with_audio = background.with_audio(voiceover)
print("Voiceover audio set to background video.")
# ----------------------------------------------------------------------

# --------------------- Step 9: Overlay Text on Video -------------------
# Overlay the text onto the video with audio
final_video = CompositeVideoClip([video_with_audio, all_text])
print("Text overlay added to video.")
# ------------------------------------------------------------------------

# --------------------- Step 10: Export Final Video ---------------------
# Export the final video to a file
final_video.write_videofile(
    FINAL_VIDEO,
    codec='libx264',
    audio_codec='mp3',
    temp_audiofile='temp-audio.mp3',
    remove_temp=True,
    fps=FPS
)
print(f"Final video exported: {FINAL_VIDEO}")
# -----------------------------------------------------------------------