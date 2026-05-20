import sys
import os
import whisperx
import difflib

# Force Python to see your FFmpeg binary
os.environ["PATH"] += os.pathsep + r"C:\Projects\bin"

def clean_word(word):
    return word.lower().strip('.,!?()[]{}"\'')

def main():
    if len(sys.argv) < 3:
        print("ERROR: Missing arguments. Usage: align.py <audio_path> <text_path> <output_srt>")
        sys.exit(1)

    audio_path = sys.argv[1]
    text_path = sys.argv[2]
    output_srt = sys.argv[3]

    # Load the user's input script
    with open(text_path, 'r', encoding='utf-8') as f:
        user_text = f.read().strip()
    user_words = user_text.split()

    device = "cpu" 

    print("[Python] Loading audio track...")
    audio = whisperx.load_audio(audio_path)
    
    # 1. TRANSCRIBE (Establish the True Audio Baseline)
    print("[Python] Transcribing audio to establish baseline...")
    asr_model = whisperx.load_model("base", device=device, compute_type="float32")
    transcribe_result = asr_model.transcribe(audio, batch_size=4)

    # 2. ALIGN (Get exact timestamps for Whisper's words)
    print("[Python] Loading phonetic alignment model...")
    align_model, metadata = whisperx.load_align_model(language_code=transcribe_result["language"], device=device)

    print("[Python] Aligning transcribed base to exact audio waveforms...")
    result = whisperx.align(transcribe_result["segments"], align_model, metadata, audio, device, return_char_alignments=False)
    
    whisper_words = []
    last_known_time = 0.0
    for segment in result["segments"]:
        if "words" in segment:
            for w in segment["words"]:
                start = w.get("start", last_known_time + 0.1)
                end = w.get("end", start + 0.3)
                last_known_time = end
                whisper_words.append({
                    "word": w["word"],
                    "start": start,
                    "end": end
                })

    # 3. GUARDED SMART MERGE
    print("[Python] Cross-referencing user text against AI baseline...")
    
    if not user_words:
        final_words = whisper_words
    else:
        w_texts = [clean_word(w["word"]) for w in whisper_words]
        u_texts = [clean_word(u) for u in user_words]

        matcher = difflib.SequenceMatcher(None, w_texts, u_texts)
        final_words = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Exact structural match: Use user's capitalization/punctuation
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    final_words.append({
                        "word": user_words[j], 
                        "start": whisper_words[i]["start"],
                        "end": whisper_words[i]["end"]
                    })
                    
            elif tag == 'replace':
                # Conflict zone: Did the user fix a typo, or paste completely wrong text?
                w_sub = " ".join(w_texts[i1:i2])
                u_sub = " ".join(u_texts[j1:j2])
                
                # Check how closely the strings match textually
                text_similarity = difflib.SequenceMatcher(None, w_sub, u_sub).ratio()
                
                if text_similarity >= 0.35: 
                    # Legitimate correction! Map user words into Whisper's time slice
                    start_time = whisper_words[i1]["start"] if i1 < len(whisper_words) else 0.0
                    end_time = whisper_words[i2-1]["end"] if i2-1 < len(whisper_words) else start_time + 0.5
                    user_segment = user_words[j1:j2]
                    duration = max(0.1, end_time - start_time)
                    time_per_word = duration / max(1, len(user_segment))
                    
                    for idx, u_word in enumerate(user_segment):
                        final_words.append({
                            "word": u_word,
                            "start": start_time + (idx * time_per_word),
                            "end": start_time + ((idx + 1) * time_per_word)
                        })
                else:
                    # Total mismatch/Gibberish detected! Reject user input, protect true audio
                    print(f"[Python] Mismatch detected. Rejecting user input block: '{u_sub}'")
                    for i in range(i1, i2):
                        final_words.append(whisper_words[i])
                        
            elif tag == 'insert':
                # User added words not heard by Whisper. Check if they are context brackets.
                user_segment = user_words[j1:j2]
                is_context = any(('[' in w or ']' in w or '(' in w or ')' in w) for w in user_segment)
                is_short_fix = len(user_segment) <= 2 # Allow small missing words (like "the", "a")
                
                if is_context or is_short_fix:
                    start_time = whisper_words[i1-1]["end"] if i1 > 0 else 0.0
                    end_time = whisper_words[i1]["start"] if i1 < len(whisper_words) else start_time + 0.5
                    if end_time <= start_time: end_time = start_time + 0.5
                    
                    duration = max(0.1, end_time - start_time)
                    time_per_word = duration / max(1, len(user_segment))
                    
                    for idx, u_word in enumerate(user_segment):
                        final_words.append({
                            "word": u_word,
                            "start": start_time + (idx * time_per_word),
                            "end": start_time + ((idx + 1) * time_per_word)
                        })
                else:
                    # Ignore large insertions that don't align with audio context
                    pass
                    
            elif tag == 'delete':
                # User skipped a word Whisper clearly heard. Retain Whisper's word for continuity.
                for i in range(i1, i2):
                    final_words.append(whisper_words[i])

    # 4. CHUNK AND WRITE SRT
    MAX_WORDS_PER_SEGMENT = 6
    caption_segments = []
    current_chunk = []

    for w in final_words:
        current_chunk.append(w)
        if len(current_chunk) >= MAX_WORDS_PER_SEGMENT:
            caption_segments.append(current_chunk)
            current_chunk = []
                
    if current_chunk:
        caption_segments.append(current_chunk)

    with open(output_srt, 'w', encoding='utf-8') as f:
        for idx, chunk in enumerate(caption_segments):
            start_time = format_timestamp(chunk[0]["start"])
            end_time = format_timestamp(chunk[-1]["end"])
            text_line = " ".join([w["word"] for w in chunk])
            f.write(f"{idx + 1}\n{start_time} --> {end_time}\n{text_line}\n\n")

    print("[Python] Guarded Smart Merge complete!")

def format_timestamp(total_seconds):
    if total_seconds < 0: total_seconds = 0.0
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int(round((total_seconds % 1) * 1000))
    
    if milliseconds >= 1000:
        milliseconds -= 1000
        seconds += 1
    if seconds >= 60:
        seconds -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        hours += 1
        
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

if __name__ == "__main__":
    main()